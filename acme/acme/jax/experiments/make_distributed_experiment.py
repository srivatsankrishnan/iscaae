# Copyright 2018 DeepMind Technologies Limited. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Program definition for a distributed layout based on a builder."""

import itertools
from typing import Any, Optional

from acme import core
from acme import environment_loop
from acme import specs
from acme.agents.jax import builders
from acme.jax import networks as networks_lib
from acme.jax import savers
from acme.jax import utils
from acme.jax.experiments import config
from acme.jax import snapshotter
from acme.utils import counting
from acme.utils import lp_utils
import jax
import launchpad as lp
import reverb

ActorId = int


def make_distributed_experiment(
    experiment: config.ExperimentConfig[builders.Networks, Any, Any],
    num_actors: int,
    *,
    num_learner_nodes: int = 1,
    num_actors_per_node: int = 1,
    multithreading_colocate_learner_and_reverb: bool = False,
    make_snapshot_models: Optional[config.SnapshotModelFactory[
        builders.Networks]] = None,
    name: str = 'agent',
    program: Optional[lp.Program] = None) -> lp.Program:
  """Builds a Launchpad program for running the experiment.

  Args:
    experiment: configuration of the experiment.
    num_actors: number of actors to run.
    num_learner_nodes: number of learner nodes to run. When using multiple
      learner nodes, make sure the learner class does the appropriate pmap/pmean
      operations on the loss/gradients, respectively.
    num_actors_per_node: number of actors per one program node. Actors within
      one node are colocated in one process.
    multithreading_colocate_learner_and_reverb: whether to colocate the learner
      and reverb nodes in one process. Not supported if the learner is spread
      across multiple nodes (num_learner_nodes > 1). False by default, which
      means no colocation.
    make_snapshot_models: a factory that defines what is saved in snapshots.
    name: name of the constructed program. Ignored if an existing program is
      passed.
    program: a program where agent nodes are added to. If None, a new program is
      created.

  Returns:
    The Launchpad program with all the nodes needed for running the experiment.
  """

  if multithreading_colocate_learner_and_reverb and num_learner_nodes > 1:
    raise ValueError(
        'Replay and learner colocation is not yet supported when the learner is'
        ' spread across multiple nodes (num_learner_nodes > 1). Please contact'
        ' Acme devs if this is a feature you want. Got:'
        '\tmultithreading_colocate_learner_and_reverb='
        f'{multithreading_colocate_learner_and_reverb}'
        f'\tnum_learner_nodes={num_learner_nodes}.')

  def build_replay():
    """The replay storage."""
    dummy_seed = 1
    spec = (
        experiment.environment_spec or
        specs.make_environment_spec(experiment.environment_factory(dummy_seed)))
    network = experiment.network_factory(spec)
    policy = config.make_policy(
        experiment=experiment,
        networks=network,
        environment_spec=spec,
        evaluation=False)
    return experiment.builder.make_replay_tables(spec, policy)

  def build_model_saver(variable_source: core.VariableSource):
    assert experiment.checkpointing
    environment = experiment.environment_factory(0)
    spec = specs.make_environment_spec(environment)
    networks = experiment.network_factory(spec)
    models = make_snapshot_models(networks, spec)
    # TODO(raveman): Decouple checkpointing and snapshotting configs.
    return snapshotter.JAXSnapshotter(
        variable_source=variable_source,
        models=models,
        path=experiment.checkpointing.directory,
        subdirectory='snapshots',
        add_uid=experiment.checkpointing.add_uid)

  def build_counter():
    counter = counting.Counter()
    if experiment.checkpointing:
      counter = savers.CheckpointingRunner(
          counter,
          key='counter',
          subdirectory='counter',
          time_delta_minutes=experiment.checkpointing.time_delta_minutes,
          directory=experiment.checkpointing.directory,
          add_uid=experiment.checkpointing.add_uid,
          max_to_keep=experiment.checkpointing.max_to_keep)
    return counter

  def build_learner(
      random_key: networks_lib.PRNGKey,
      replay: reverb.Client,
      counter: Optional[counting.Counter] = None,
      primary_learner: Optional[core.Learner] = None,
  ):
    """The Learning part of the agent."""

    dummy_seed = 1
    spec = (
        experiment.environment_spec or
        specs.make_environment_spec(experiment.environment_factory(dummy_seed)))

    # Creates the networks to optimize (online) and target networks.
    networks = experiment.network_factory(spec)

    iterator = experiment.builder.make_dataset_iterator(replay)
    # make_dataset_iterator is responsible for putting data onto appropriate
    # training devices, so here we apply prefetch, so that data is copied over
    # in the background.
    iterator = utils.prefetch(iterable=iterator, buffer_size=1)
    counter = counting.Counter(counter, 'learner')
    learner = experiment.builder.make_learner(random_key, networks, iterator,
                                              experiment.logger_factory, spec,
                                              replay, counter)

    if experiment.checkpointing:
      if primary_learner is None:
        learner = savers.CheckpointingRunner(
            learner,
            key='learner',
            subdirectory='learner',
            time_delta_minutes=5,
            directory=experiment.checkpointing.directory,
            add_uid=experiment.checkpointing.add_uid,
            max_to_keep=experiment.checkpointing.max_to_keep)
      else:
        learner.restore(primary_learner.save())
        # NOTE: This initially synchronizes secondary learner states with the
        # primary one. Further synchronization should be handled by the learner
        # properly doing a pmap/pmean on the loss/gradients, respectively.

    return learner

  def build_actor(
      random_key: networks_lib.PRNGKey,
      replay: reverb.Client,
      variable_source: core.VariableSource,
      counter: counting.Counter,
      actor_id: ActorId,
  ) -> environment_loop.EnvironmentLoop:
    """The actor process."""
    environment_key, actor_key = jax.random.split(random_key)
    # Create environment and policy core.

    # Environments normally require uint32 as a seed.
    environment = experiment.environment_factory(
        utils.sample_uint32(environment_key))
    environment_spec = specs.make_environment_spec(environment)

    networks = experiment.network_factory(environment_spec)
    policy_network = config.make_policy(
        experiment=experiment,
        networks=networks,
        environment_spec=environment_spec,
        evaluation=False)
    adder = experiment.builder.make_adder(replay, environment_spec,
                                          policy_network)
    actor = experiment.builder.make_actor(actor_key, policy_network,
                                          environment_spec, variable_source,
                                          adder)

    # Create logger and counter.
    counter = counting.Counter(counter, 'actor')
    logger = experiment.logger_factory('actor', counter.get_steps_key(),
                                       actor_id)
    # Create the loop to connect environment and agent.
    return environment_loop.EnvironmentLoop(
        environment, actor, counter, logger, observers=experiment.observers)

  if not program:
    program = lp.Program(name=name)

  key = jax.random.PRNGKey(experiment.seed)

  checkpoint_time_delta_minutes: Optional[int] = (
      experiment.checkpointing.replay_checkpointing_time_delta_minutes
      if experiment.checkpointing else None)
  replay_node = lp.ReverbNode(
      build_replay, checkpoint_time_delta_minutes=checkpoint_time_delta_minutes)
  replay = replay_node.create_handle()

  counter = program.add_node(lp.CourierNode(build_counter), label='counter')

  if experiment.max_num_actor_steps is not None:
    program.add_node(
        lp.CourierNode(lp_utils.StepsLimiter, counter,
                       experiment.max_num_actor_steps),
        label='counter')

  learner_key, key = jax.random.split(key)
  learner_node = lp.CourierNode(build_learner, learner_key, replay, counter)
  learner = learner_node.create_handle()
  variable_sources = [learner]

  if multithreading_colocate_learner_and_reverb:
    program.add_node(
        lp.MultiThreadingColocation([learner_node, replay_node]),
        label='learner')
  else:
    program.add_node(replay_node, label='replay')

    with program.group('learner'):
      program.add_node(learner_node)

      # Maybe create secondary learners, necessary when using multi-host
      # accelerators.
      # Warning! If you set num_learner_nodes > 1, make sure the learner class
      # does the appropriate pmap/pmean operations on the loss/gradients,
      # respectively.
      for _ in range(1, num_learner_nodes):
        learner_key, key = jax.random.split(key)
        variable_sources.append(
            program.add_node(
                lp.CourierNode(
                    build_learner, learner_key, replay,
                    primary_learner=learner)))
        # NOTE: Secondary learners are used to load-balance get_variables calls,
        # which is why they get added to the list of available variable sources.
        # NOTE: Only the primary learner checkpoints.
        # NOTE: Do not pass the counter to the secondary learners to avoid
        # double counting of learner steps.

  with program.group('actor'):
    # Create all actor threads.
    *actor_keys, key = jax.random.split(key, num_actors + 1)
    variable_sources = itertools.cycle(variable_sources)
    actor_nodes = [
        lp.CourierNode(build_actor, akey, replay, vsource, counter, aid)
        for aid, (akey,
                  vsource) in enumerate(zip(actor_keys, variable_sources))
    ]

    # Create (maybe colocated) actor nodes.
    if num_actors_per_node == 1:
      for actor_node in actor_nodes:
        program.add_node(actor_node)
    else:
      for i in range(0, num_actors, num_actors_per_node):
        program.add_node(
            lp.MultiThreadingColocation(actor_nodes[i:i + num_actors_per_node]))

  for evaluator in experiment.get_evaluator_factories():
    evaluator_key, key = jax.random.split(key)
    program.add_node(
        lp.CourierNode(evaluator, evaluator_key, learner, counter,
                       experiment.builder.make_actor),
        label='evaluator')

  if make_snapshot_models and experiment.checkpointing:
    program.add_node(
        lp.CourierNode(build_model_saver, learner), label='model_saver')

  return program