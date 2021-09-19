# Python libraries
import networkx as nx


def get_delay(origin: object, target: object) -> int:
    """Gets the distance (in terms of delay) between two elements (origin and target).

    Args:
        origin (object): Origin object.
        target (object): Target object.

    Returns:
        int: Delay between origin and target.
    """
    topology = origin.simulator.topology

    path = nx.shortest_path(G=topology, source=origin.base_station, target=target.base_station, weight="delay")
    delay = topology.calculate_path_delay(path=path) + topology.wireless_delay

    return delay
