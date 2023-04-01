# Architecture Gym (ArchGym)
### An OpenAI Gym Interface for Computer Architecture Research

Architecture Gym (ArchGym) is a systematic and standardized framework for ML-driven research tackling architectural design space exploration.
ArchGym currently supports five different ML-based search algorithms and three unique architecture simulators. The framework is built with the ability to be easily extended to support brand-new search algorithms and architecture simulators via a standardized interface.

![Alt text](./docs/ArchGym_Framework_Overview.png?raw=true "Title")

## Agents
We define “agent” as an encapsulation of the machine learning algorithm. An ML algorithm consists of “hyperparameters” and a guiding “policy”. 
We currently support the following agents:
- Ant Colony Optimization (ACO)
- Genetic Algorithm (GA)
- Bayesian Optimization (BO)
- Reinforcement Learning (RL)
- Random Walker (RW)

## Environments (Simulators + Workloads)
Each environment is an encapsulation of the architecture cost model and the workload. The architecture cost model determines the cost of running the workload for a given set of architecture parameters. For example, the cost can be latency, throughput, area, or energy or any combination.
We currently support the following Gym Environments:
- DRAMGym     (DRAMSys Simulator + Memory Trace Workloads)
- TimeloopGym (Timeloop Simulator + CNN Workloads)
- FARSIGym    (FARSI Simulator + AR/VR Workloads)

## Getting Started 

### Docker Setup
A `Dockerfile` is also provided for each simulator to get up and running quickly in a containerized environment. 
In `arch-gym/sims` each simulator (i.e., DRAMSys, Timeloop, FARSI) has a `build.sh` that can be used to build the docker container.
Then if you simply bring up and enter this instance, you can invoke any of the training scripts via python to test right away! 

For example for setting up FARSIGym via Docker you would follow these steps:
1. `cd arch-gym/sims/FARSI_sim`
2. `./build.sh`
3. `docker run --entrypoint /bin/bash -it farsi_archgym:latest`
4. `python train_aco_FARSIEnv.py`

If all is setup correctly, you should see the output of the `BEST ANT DURING ITERATION`.

### Native Installation
In order to use Arch-Gym, you will first need to set up a conda environment and install `requirements.txt`.

Then depending on your choice of backend (i.e. DRAMSys, Timeloop, FARSI), you will need to follow the steps below.  

#### DRAMSys Setup
The next step is setting up DRAMSys, a memory simulator, used by Arch-Gym.

Follow the steps below to do so:  
1. Build DRAMSys (performed on Ubuntu 18.04):  
  * Recursively clone the DRAMSys repo using the following command:  `git clone --recursive git@github.com:tukl-msd/DRAMSys.git`
  * DRAMSys uses CMake for the build process, the minimum required version is CMake 3.10. Use.  `cmake --version` to make sure you have the minimum required version installed.  
  * Build the standalone simulator running the following:  
  ```
  $ cd DRAMSys
  $ mkdir build
  $ cd build
  $ cmake ../DRAMSys/
  $ make
  ```
  * Check to make sure the build succeeded:
  ```
  $ cd simulator
  $ ./DRAMSys
  ```  
  You should see the simulation complete (i.e. reaching 100%) if installed correctly.  
 
2. Use arch-gym modified binary of DRAMSys:  
  * In the arch gym repo copy the binary at the following path `arch-gym/sims/DRAM/binary/DRAMSys` and replace the binary in the DRAMSys repo in `DRAMSys/build/simulator/DRAMSys`.  
  * Attempt running this modified version of the binary now by running `./DRAMSys` and see the simulation successfully complete (i.e. reaching 100%).  

3. Modify `arch-gym/configs/configs.py`:
  * The beginning of these four string variables in `configs.py`: `dram_mem_controller_config`, `exe_path`, `sim_config`, and `logdir` need to be modified to point to the relative path of your local arch-gym repo for your setup.  

4. Test to make sure everything is working:  
  * Navigate to the root of the repo and run `python train_aco_DRAMSys.py`.
  * If all is setup correctly, you should see the output of the `BEST ANT DURING ITERATION`.
  * If not, you may need to check to make sure you have all the necessary dependencies installed. 

#### Timeloop Setup
*Coming Soon*

#### FARSI Setup
*Coming Soon*
