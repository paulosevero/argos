# pylint: disable=invalid-name
"""Contains the basic structure necessary to execute the simulation.
"""
# EdgeSimPy components
from edge_sim_py.simulator import Simulator
from edge_sim_py.components.topology import Topology
from edge_sim_py.components.base_station import BaseStation
from edge_sim_py.components.user import User
from edge_sim_py.components.application import Application
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.service import Service
from edge_sim_py.component_builders.distributions_builder import uniform

# Importing Argos and baseline algorithms
from argos.faticanti2020 import faticanti2020
from argos.argos import argos
from edge_sim_py.heuristics.never_migrate import never_migrate
from edge_sim_py.heuristics.follow_vehicle import follow_vehicle

# Python libraries
import random
import time
import typing


def add_privacy_requirements():
    # Defining privacy requirements for services based on an uniform distribution
    privacy_requirements = uniform(n_items=Service.count(), valid_values=[True, False], shuffle_distribution=True)

    for service in Service.all():
        # Defining the 'privacy_requirement' attribute
        service.privacy_requirement = privacy_requirements[service.id - 1]


def add_trusted_servers():
    # Defining the number of trusted servers per user based on an uniform distribution
    number_of_trusted_servers = uniform(n_items=User.count(), valid_values=[15, 30], shuffle_distribution=True)

    # Assigning trusted servers of each user
    for user in User.all():
        # Defining the 'trusted_servers' attribute (randomly pick servers that will be trusted by the user)
        user.trusted_servers = [random.choice(EdgeServer.all()) for _ in range(number_of_trusted_servers[user.id - 1])]


def run(self, algorithm: typing.Callable):
    """Executes the simulation.

    Args:
        algorithm (typing.Callable): Algorithm that will be executed during simulation.
    """
    objects = Topology.all() + BaseStation.all() + EdgeServer.all() + Application.all() + Service.all() + User.all()
    for obj in objects:
        obj.simulator = self

    # Adding a reference to the network topology inside the Simulator instance
    self.topology = Topology.first()

    # Creating an empty list to accommodate the simulation metrics
    algorithm_name = f"{str(algorithm).split(' ')[1]}-{time.time()}"
    self.metrics[algorithm_name] = []

    # Storing original objects state
    self.store_original_state()

    # Iterating over simulation time steps
    for simulation_step in range(1, self.simulation_steps + 1):
        # Updating system state according to the new simulation time step
        self.update_state(step=simulation_step)

        # Collecting metrics for the current simulation step
        self.collect_metrics(algorithm=algorithm_name)

        # Executing user-specified algorithm
        algorithm()

    # Collecting metrics after the algorithm execution in the last simulation step
    self.collect_metrics(algorithm=algorithm_name)

    # Restoring original objects state
    self.restore_original_state()


def collect_metrics(self, algorithm: str):
    """Collects simulation metrics.

    Args:
        algorithm (str): Name of the algorithm being executed.
    """
    sla_violations = 0
    services_on_trusted_servers = 0
    privacy_violations = 0
    migrations = 0

    # Computing user-related metrics (SLA violations)
    for user in User.all():
        for app in user.applications:
            if user.delays[app] > user.delay_slas[app]:
                sla_violations += 1

    # Computing services-related metrics (Services on trusted servers, Privacy violations, Number of migrations)
    for service in Service.all():
        user = service.application.users[0]
        if service.server in user.trusted_servers:
            services_on_trusted_servers += 1
        elif service.server not in user.trusted_servers and service.privacy_requirement:
            privacy_violations += 1

        # As the metrics collection method is called before the algorithm execution, we need to compute the number of
        # migrations performed in the previous step.
        for migration in service.migrations:
            if (
                migration["step"] == self.current_step - 1
                or self.current_step == self.simulation_steps
                and migration["step"] == self.current_step
            ):
                migrations += 1

    # Creating the structure to accommodate simulation metrics
    self.metrics[algorithm].append(
        {
            "step": self.current_step,
            "sla_violations": sla_violations,
            "migrations": migrations,
            "privacy_violations": privacy_violations,
            "services_on_trusted_servers": services_on_trusted_servers,
        }
    )


def show_results(self):
    """Displays the simulation results."""
    for algorithm, results in self.metrics.items():

        sla_violations = 0
        services_on_trusted_servers = 0
        privacy_violations = 0
        migrations = 0

        for step_results in results:
            sla_violations += step_results["sla_violations"]
            services_on_trusted_servers += step_results["services_on_trusted_servers"]
            privacy_violations += step_results["privacy_violations"]
            migrations += step_results["migrations"]

        print(f"Algorithm: {algorithm}")
        print(f"    SLA violations: {sla_violations}")
        print(f"    Privacy Violations: {privacy_violations}")
        print(f"    Migrations: {migrations}")
        print(f"    Services on Trusted Servers: {services_on_trusted_servers}")


def main():
    random.seed(1)

    # Overriding the methods that collect and display simulation results to comprehend privacy-related metrics
    Simulator.run = run
    Simulator.collect_metrics = collect_metrics
    Simulator.show_results = show_results

    # Creating an instance of EdgeSimPy simulator
    simulator = Simulator()

    # Loading the dataset
    simulator.load_dataset(input_file="datasets/paper.json")

    # Extending the simulated objects with privacy/trustworthiness attributes
    add_privacy_requirements()
    add_trusted_servers()

    # Running the simulation
    simulator.run(algorithm=never_migrate)
    simulator.run(algorithm=follow_vehicle)
    simulator.run(algorithm=faticanti2020)
    simulator.run(algorithm=argos)

    # Displaying simulation results
    simulator.show_results()


if __name__ == "__main__":
    main()
