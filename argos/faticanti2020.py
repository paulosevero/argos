# EdgeSimPy components
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.service import Service

# Helper methods
from argos.helper_methods import get_delay


def faticanti2020():
    """Adapted version of [1], that focuses on finding host servers for microservice-based applications on
    Edge Computing scenarios with multiple infrastructure providers. This heuristic was originally designed to define
    service's deployment (i.e., initial placement). The code below is an adapted version that uses the heuristic's
    original reasoning to perform service migration when it detects application's SLA are violated.

    References:
        [1] Faticanti, Francescomaria, et al. "Deployment of Application Microservices in Multi-Domain Federated
        Fog Environments." International Conference on Omni-layer Intelligent Systems (COINS). IEEE, 2020.
    """

    # Based on Faticanti's idea, we sort services based on their positions in their application's service chain and
    # according to their applications's network demand (services from applications with lower demand come first).
    services = sorted(
        Service.all(),
        key=lambda service: (service.application.services.index(service), service.application.network_demand),
    )

    for service in services:
        # Gathering service's application and current application's delay
        app = service.application
        user = app.users[0]
        delay = user.delays[app]
        sla = user.delay_slas[app]

        # Faticanti's heuristic was originally designed to define initial service placement. As we perform migrations
        # based on users mobility, we modify the heuristic to just relocate services when their application's SLA is
        # violated so that the heuristic avoids performing unnecessary migrations. Without such modification, the
        # heuristic would try to migrate services in all time steps, which would lead to poor results in our scenario.
        if delay > sla:
            # Sorting edge servers by: trustworthiness, distance from user (in terms of delay), and free resources.
            edge_servers = sorted(
                EdgeServer.all(),
                key=lambda s: (
                    -(s in user.trusted_servers),
                    get_delay(origin=user, target=s),
                    s.capacity - s.demand,
                ),
            )

            # Greedily iterating over the list of EdgeNode
            # candidates to find the best node to host the service
            for edge_server in edge_servers:
                if service.server == edge_server:
                    break

                elif edge_server.capacity >= edge_server.demand + service.demand:
                    service.migrate(target_server=edge_server)
                    user.set_communication_path(app=app)
                    break
