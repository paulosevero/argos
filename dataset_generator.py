"""Contains a set of methods used to create datasets for the simulator.

Objects are created using a group of "builders",
classes that implement the Builder design pattern to instantiate objects with different properties in an organized way.
More information about the Builder design pattern can be found in the links below:
- https://refactoring.guru/design-patterns/builder
- https://refactoring.guru/design-patterns/builder/python/example
"""
# Python libraries
import random
import json

# EdgeSimPy components
from edge_sim_py.simulator import Simulator
from edge_sim_py.components.base_station import BaseStation
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.application import Application
from edge_sim_py.components.service import Service
from edge_sim_py.components.topology import Topology
from edge_sim_py.components.user import User

# Helper builders
from edge_sim_py.component_builders.map_builder import create_hexagonal_grid
from edge_sim_py.component_builders.distributions_builder import uniform
from edge_sim_py.component_builders.placements_builder import first_fit

# Component builders
from edge_sim_py.component_builders.base_station_builder import BaseStationBuilder
from edge_sim_py.component_builders.edge_server_builder import EdgeServerBuilder
from edge_sim_py.component_builders.application_builder import ApplicationBuilder
from edge_sim_py.component_builders.service_builder import ServiceBuilder
from edge_sim_py.component_builders.user_builder import UserBuilder


VERBOSE = True

# Defining seed values to enable reproducibility
SEED = 1
random.seed(SEED)


# Defining number of simulation steps
simulation_steps = 30

# Creating list of hexagons to represent the map
map_coordinates = create_hexagonal_grid(x_size=10, y_size=10)

# Creating base stations
n_base_stations = len(map_coordinates)
base_station_builder = BaseStationBuilder()
base_station_builder.create_objects(n_objects=n_base_stations)
base_station_builder.set_coordinates_all_base_stations(coordinates=map_coordinates)

# Creating edge servers
n_edge_servers = 60
edge_server_builder = EdgeServerBuilder()
edge_server_builder.create_objects(n_objects=n_edge_servers)
edge_servers_coordinates = random.sample(map_coordinates, n_edge_servers)
edge_server_builder.set_coordinates_all_edge_servers(coordinates=edge_servers_coordinates)
edge_servers_capacity = uniform(n_items=n_edge_servers, valid_values=[100, 200], shuffle_distribution=True)
edge_server_builder.set_capacity_all_edge_servers(capacity_values=edge_servers_capacity)

# Creating applications and services (and defining relationships between them)
n_applications = 120
application_builder = ApplicationBuilder()
application_builder.create_objects(n_objects=n_applications)
network_demands = uniform(n_items=n_applications, valid_values=[2, 4], shuffle_distribution=True)
application_builder.set_network_demand_all_applications(network_demands=network_demands)

services_per_application = uniform(n_items=n_applications, valid_values=[2], shuffle_distribution=True)

n_services = sum(services_per_application)
service_builder = ServiceBuilder()
service_builder.create_objects(n_objects=n_services)
service_demands = uniform(n_items=n_services, valid_values=[10, 20, 30, 40, 50], shuffle_distribution=True)
service_builder.set_demand_all_services(demand_values=service_demands)

for index, application in enumerate(Application.all()):
    for _ in range(services_per_application[index]):
        service = next((service for service in Service.all() if service.application is None), None)
        if service is not None:
            service.application = application
            application.services.append(service)

# Defines the initial service placement scheme
first_fit()


# Creating network topology
network_nodes = BaseStation.all()
topology = Topology.new_barabasi_albert(
    nodes=network_nodes,
    seed=SEED,
    delay=5,
    wireless_delay=10,
    bandwidth=10,
    min_links_per_node=2,
)


# Creating users
n_users = n_applications
user_builder = UserBuilder()
user_builder.create_objects(n_objects=n_users)
user_builder.set_target_positions(map_coordinates=map_coordinates, n_target_positions=50)
user_builder.set_pathway_mobility_all_users(
    map_coordinates=map_coordinates, steps=simulation_steps, target_positions=False
)

users_per_application = uniform(n_items=n_users, valid_values=[1], shuffle_distribution=True)

for index, user in enumerate(User.all()):
    delay_slas = uniform(
        n_items=users_per_application[index],
        valid_values=[60, 120],
        shuffle_distribution=True,
    )

    for i in range(users_per_application[index]):
        application = next(
            (application for application in Application.all() if len(application.users) <= i),
            None,
        )
        if application is not None:
            application.users.append(user)
            user.applications.append(application)
            user.delay_slas[application] = delay_slas[i]

            user.communication_paths[application] = []
            communication_chain = [user] + application.services

            # Defining a set of links to connect the items in the application's service chain
            for j in range(len(communication_chain) - 1):

                # Defining origin and target nodes
                origin = (
                    user.base_station if communication_chain[j] == user else communication_chain[j].server.base_station
                )
                target = (
                    user.base_station
                    if communication_chain[j + 1] == user
                    else communication_chain[j + 1].server.base_station
                )
                # Finding the best communication path
                path = Topology.first().get_shortest_path(
                    origin=origin,
                    target=target,
                    user=user,
                    app=application,
                )
                # Adding the best path found to the communication path
                user.communication_paths[application].extend(path)

            # Removing duplicated entries in the communication path to avoid NetworkX crashes
            user.communication_paths[application] = Topology.first().remove_path_duplicates(
                path=user.communication_paths[application]
            )

            # Computing the new demand of chosen links
            Topology.first().allocate_communication_path(
                communication_path=user.communication_paths[application],
                app=application,
            )

            # Initializes the application's delay with the time it takes to communicate its client and a base station
            delay = Topology.first().wireless_delay

            # Adding the communication path delay to the application's delay
            communication_path = user.communication_paths[application]
            delay += Topology.first().calculate_path_delay(path=communication_path)

            # Updating application delay inside user's 'applications' attribute
            user.delays[application] = delay

if VERBOSE:
    print("\nBase Stations:")
    for base_station in BaseStation.all():
        print(f"    {base_station}. Coordinates: {base_station.coordinates}.")

    print("\n\nEdge Servers:")
    for edge_server in EdgeServer.all():
        print(
            f"    {edge_server}. Coordinates: {edge_server.coordinates}. Capacity: {edge_server.capacity}. Base Station: {edge_server.base_station} ({edge_server.base_station.coordinates})"
        )

    print("\n\nApplications:")
    for application in Application.all():
        print(f"    {application}. Network Demand: {application.network_demand}.")
        for service in application.services:
            print(f"        {service}. Demand: {service.demand}. Server: {service.server}")

    print("\n\nUsers:")
    for user in User.all():
        print(
            f"    {user}. Coordinates: {user.coordinates}. Base Station: {user.base_station} ({user.base_station.coordinates})"
        )

        for app in user.applications:
            print(
                f"        {app}. SLA: {user.delay_slas[app]}. Delay {user.delays[app]}. Communication Path: {len(user.communication_paths[app])}"
            )


##########################
## CREATING OUTPUT FILE ##
##########################
# Creating dataset dictionary that will be converted to a JSON object
dataset = {}


# General information
dataset["simulation_steps"] = simulation_steps
dataset["coordinates_system"] = "hexagonal_grid"

dataset["base_stations"] = [
    {
        "id": base_station.id,
        "coordinates": base_station.coordinates,
        "users": [user.id for user in base_station.users],
        "edge_servers": [edge_server.id for edge_server in base_station.edge_servers],
    }
    for base_station in BaseStation.all()
]

dataset["edge_servers"] = [
    {
        "id": edge_server.id,
        "capacity": edge_server.capacity,
        "base_station": edge_server.base_station.id,
        "coordinates": edge_server.coordinates,
        "services": [service.id for service in edge_server.services],
    }
    for edge_server in EdgeServer.all()
]

dataset["users"] = [
    {
        "id": user.id,
        "base_station": {"type": "BaseStation", "id": user.base_station.id},
        "applications": [
            {
                "id": app.id,
                "delay_sla": user.delay_slas[app],
                "communication_path": [
                    {"type": "BaseStation", "id": base_station.id} for base_station in user.communication_paths[app]
                ],
            }
            for app in user.applications
        ],
        "coordinates_trace": user.coordinates_trace,
    }
    for user in User.all()
]

dataset["applications"] = [
    {
        "id": application.id,
        "network_demand": application.network_demand,
        "services": [service.id for service in application.services],
        "users": [user.id for user in application.users],
    }
    for application in Application.all()
]

dataset["services"] = [
    {
        "id": service.id,
        "demand": service.demand,
        "server": {
            "type": "EdgeServer",
            "id": service.server.id if service.server else None,
        },
        "application": service.application.id,
    }
    for service in Service.all()
]

network_links = []
for index, link in enumerate(Topology.first().edges(data=True)):
    nodes = [
        {"type": "BaseStation", "id": link[0].id},
        {"type": "BaseStation", "id": link[1].id},
    ]
    delay = Topology.first()[link[0]][link[1]]["delay"]
    bandwidth = Topology.first()[link[0]][link[1]]["bandwidth"]
    network_links.append({"id": index + 1, "nodes": nodes, "delay": delay, "bandwidth": bandwidth})

dataset["network"] = {
    "wireless_delay": Topology.first().wireless_delay,
    "links": network_links,
}

# Defining output file name
dataset_file_name = "scenario1"

# Storing the dataset to an output file
with open(f"datasets/{dataset_file_name}.json", "w") as output_file:
    json.dump(dataset, output_file, indent=4)
