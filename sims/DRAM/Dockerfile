# Dockerfile for Arch-Gym project for other agents (BO, ACO, GA, RW)
# start with miniconda image

FROM continuumio/miniconda3
RUN if ! id 1000; then useradd -m -u 1000 clouduser; fi
RUN mkdir /workdir
WORKDIR /workdir
RUN echo "Clone Arch-Gym Repo!"
RUN git clone --recursive https://github.com/srivatsankrishnan/iscaae.git


RUN cd iscaae && conda env create -f environment.yml
RUN apt update && apt install -y build-essential
# Make RUN commands use the new environment:
RUN echo "conda activate arch-gym" >> ~/.bashrc
SHELL ["/bin/bash", "--login", "-c"]

# Install the acme package
RUN cd iscaae/acme && pip install .[jax,tf,testing,envs] && pip install envlogger[tfds] && apt-get update && apt-get -y install libgmp-dev && pip install scikit-optimize

# The code to run when container is started:

RUN chown -R 1000:root /workdir && chmod -R 775 /workdir
WORKDIR /workdir/iscaae/sims/DRAM
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/conda/envs/arch-gym/lib
RUN echo $LD_LIBRARY_PATH
ENTRYPOINT ["conda", "run", "-n", "arch-gym", "python", "launch_gcp.py"]