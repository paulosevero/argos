# EdgeSimPy components
from edge_sim_py.components.user import User
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.application import Application

# Helper methods
from argos.helper_methods import get_delay


def argos():
    """Privacy-aware service migration strategy for edge computing environments."""

    apps = sorted(Application.all(), key=lambda app: app.users[0].delay_slas[app] - app.users[0].delays[app])

    for app in apps:
        user = app.users[0]
        delay = user.delays[app]
        sla = user.delay_slas[app]

        # We only migrate services from applications whose SLA is violated at the current simulation time step.
        if delay > sla:

            host_candidates = get_host_candidates(user=user)

            services = sorted(app.services, key=lambda s: -s.demand)
            services = app.services
            allocation_insights = get_allocation_insights(user=user, services=services)

            for service in services:
                if allocation_insights[service]:
                    host_candidates = sorted(
                        host_candidates,
                        key=lambda c: (
                            -c["is_trusted"],
                            c["delay"],
                            c["trusted_users"],
                        ),
                    )
                else:
                    host_candidates = sorted(
                        host_candidates,
                        key=lambda c: (
                            c["delay"],
                            c["trusted_users"],
                        ),
                    )

                # Greedily iterating over the list of edge servers to find a host for the service
                for edge_server_metadata in host_candidates:
                    edge_server = edge_server_metadata["object"]

                    if service.server == edge_server:
                        break

                    elif edge_server.capacity >= edge_server.demand + service.demand:
                        service.migrate(target_server=edge_server)
                        break

            user.set_communication_path(app=app)


def get_allocation_insights(user: object, services: list) -> list:
    """Checks if a list of services could be hosted by trusted servers.

    Args:
        user (object): User object.
        services (list): List of services to be allocated.

    Returns:
        list: Allocation insights that inform if services could be hosted by trusted servers.
    """
    allocation_insights = {}

    # Gathering the list of trustworthy edge servers and sorting them based on their amount of resources available
    edge_servers = [server for server in EdgeServer.all() if server in user.trusted_servers]
    edge_servers = sorted(edge_servers, key=lambda server: server.capacity - server.demand)

    # Iterating over the list of services to check which of them could be hosted by trustworthy nodes
    for service in services:
        host_found = False
        for edge_node in edge_servers:
            if edge_node.capacity >= edge_node.demand + service.demand:
                host_found = True
                edge_node.demand += service.demand
                allocation_insights[service] = True
                break
        if not host_found:
            allocation_insights[service] = False

    # Recomputing the demand of edge servers to preserve simulation's consistency
    for edge_node in edge_servers:
        edge_node.compute_demand()

    return allocation_insights


def get_host_candidates(user: object) -> list:
    """Get list of host candidates for hosting services of a given user.

    Args:
        user (object): User object.

    Returns:
        list: List of host candidates.
    """
    host_candidates = []

    for edge_server in EdgeServer.all():
        delay = get_delay(origin=user, target=edge_server)
        trusted_users = sum([1 for u in User.all() if edge_server in u.trusted_servers and u != user])
        is_trusted = edge_server in user.trusted_servers

        host_candidates.append(
            {
                "object": edge_server,
                "delay": delay,
                "trusted_users": trusted_users,
                "is_trusted": int(is_trusted),
            }
        )

    return host_candidates
