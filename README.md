## Latency-Aware Privacy-Preserving Service Migration in Federated Edges

> This repository presents Argos, a resource management strategy designed for migrating microservice-based applications according to users' mobility in federated edge computing infrastructures while considering services' privacy requirements and users' trust levels on infrastructure providers.


### Motivation

There has been considerable prior work regarding resource allocation in federated edge computing scenarios considering applications' privacy. However, existing solutions present some significant shortcomings. For example:

- Most strategies equalize the level of trust of entire regions while making allocation decisions, overlooking the existence of servers managed by different providers in the same region with possibly different levels of trust.
- Existing solutions assume the same privacy requirements for all microservices from an application, neglecting that microservices with different responsibilities may have distinct privacy requirements (e.g., database microservices may demand more privacy than front-end microservices).

To fill this gap, Argos performs mobility-aware migrations in federated edges according to privacy and performance requirements of microservices to reinforce the applications' security while delivering the expected performance levels.

### Repository Structure

Within the repository, you'll find the following directories and files, logically grouping common assets used to simulate microservice migrations on federated edge computing infrastructures. You'll see something like this:

```
├── argos/
│   ├── argos.py
│   ├── faticanti2020.py
│   ├── helper_methods.py
│   └── __main__.py
├── dataset_generator.py
├── datasets/
├── edge_sim_py-0.1.0-py3-none-any.whl
├── poetry.lock
└── pyproject.toml
```

In the root directory, the `pyproject.toml` file organizes all project dependencies, including the minimum required version of the Python language and the "whl" file containing the simulator core (i.e., `edge_sim_py-0.1.0-py3-none-any.whl`). The `pyproject.toml` file guides the execution of Poetry, a Python library which installs the simulator securely, avoiding conflicts with external dependencies.

> Modifications made to the pyproject.toml file are automatically inserted into poetry.lock whenever Poetry is called.

The "datasets" directory contains JSON files describing the components that will be simulated during the experiments. We can create custom datasets modifying the `dataset_generator.py` file.

The "argos" directory accommodates the source code for the migration strategies used in the simulator (i.e., argos.py and faticanti2020.py) and helper methods that extend the standard functionality of the simulated components (i.e., helper_methods.py). 



### Installation Guide

Project dependencies are available for Linux, Windows and MacOS. However, we highly recommend using a recent version of a Debian-based Linux distribution. The installation below was validated on **Ubuntu 20.04.3 LTS**.

#### Prerequisites

The first step needed to run the simulation is installing some basic packages. We can do that by executing the following command:

```bash
sudo apt install libopenblas-dev liblapack-dev libxml2-dev libxmlsec1-dev
```

We use a Python library called Poetry to manage project dependencies. In addition to selecting and downloading proper versions of project dependencies, Poetry automatically provisions virtual environments for the simulator, avoiding problems with external dependencies. On Linux and MacOS, we can install Poetry with the following command:

```bash
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```

The command above installs Poetry executable inside Poetry’s bin directory. On Unix it is located at `$HOME/.poetry/bin`. We can get more information about Poetry installation at: https://python-poetry.org/docs/#installation.

#### Configuration

Considering that we already downloaded the repository, the first thing we need to do is install dependencies using Poetry. To do so, we access the command line in the root directory and type the following command:

```bash
poetry shell
```

The command we just ran creates a virtual Python environment that we will use to run the simulator. Notice that Poetry automatically sends us to the newly created virtual environment. Next, we need to install the project dependencies using the following command:

```bash
poetry install
```

After a few moments, Poetry will have installed all the dependencies needed by the simulator and we will be ready to run the experiments.

### Usage Guide

Our simulator works primarily based on the content of the `__main__.py` file. Therefore, if you want to change which algorithms are executed during the simulation, you just need to change that file. To run all migration strategies, execute the following command:

```bash
python3 -B -m argos
```

### How to Cite

To be defined.
