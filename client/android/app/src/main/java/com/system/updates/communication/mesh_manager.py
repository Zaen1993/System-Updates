import networkx as nx
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class MeshManager:
    """
    Mesh network manager for peer-to-peer communication between devices.
    Uses graph theory to manage connections and route data.
    """
    def __init__(self):
        self.graph = nx.Graph()
        self.device_info = {}

    def add_device(self, device_id: str, neighbors: List[str] = None, metadata: Dict[str, Any] = None) -> None:
        """
        Add a device to the mesh network with optional neighbors and metadata.
        """
        if neighbors is None:
            neighbors = []
        self.graph.add_node(device_id)
        self.device_info[device_id] = metadata or {}
        for neighbor in neighbors:
            self.graph.add_edge(device_id, neighbor)
        logger.info(f"Device {device_id} added to mesh with neighbors {neighbors}")

    def remove_device(self, device_id: str) -> None:
        """
        Remove a device and all its connections from the mesh.
        """
        if device_id in self.graph:
            self.graph.remove_node(device_id)
            self.device_info.pop(device_id, None)
            logger.info(f"Device {device_id} removed from mesh")

    def update_neighbors(self, device_id: str, neighbors: List[str]) -> None:
        """
        Update the neighbor list for a device (replace old edges with new ones).
        """
        if device_id not in self.graph:
            self.add_device(device_id, neighbors)
            return
        # Remove old edges
        current_neighbors = list(self.graph.neighbors(device_id))
        for n in current_neighbors:
            if n not in neighbors:
                self.graph.remove_edge(device_id, n)
        # Add new edges
        for n in neighbors:
            if n != device_id and not self.graph.has_edge(device_id, n):
                self.graph.add_edge(device_id, n)
        logger.info(f"Device {device_id} neighbors updated to {neighbors}")

    def find_route(self, source: str, target: str) -> Optional[List[str]]:
        """
        Find the shortest path between two devices.
        Returns list of device IDs including source and target, or None if no path.
        """
        try:
            path = nx.shortest_path(self.graph, source=source, target=target)
            logger.debug(f"Route found from {source} to {target}: {path}")
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            logger.warning(f"No route between {source} and {target}")
            return None

    def find_all_routes(self, source: str, target: str, max_hops: int = 10) -> List[List[str]]:
        """
        Find all simple paths (up to max_hops) between two devices.
        """
        try:
            paths = list(nx.all_simple_paths(self.graph, source=source, target=target, cutoff=max_hops))
            logger.debug(f"Found {len(paths)} routes from {source} to {target}")
            return paths
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def route_data(self, data: Any, path: List[str]) -> bool:
        """
        Simulate routing data along a given path.
        In a real implementation, this would actually send data hop-by-hop.
        """
        if not path or len(path) < 2:
            logger.error("Invalid path for routing")
            return False
        logger.info(f"Routing data through: {' -> '.join(path)}")
        # Here we would implement actual transmission logic (e.g., via sockets, BLE, etc.)
        return True

    def get_neighbors(self, device_id: str) -> List[str]:
        """
        Return list of neighbors for a given device.
        """
        if device_id in self.graph:
            return list(self.graph.neighbors(device_id))
        return []

    def get_all_devices(self) -> List[str]:
        """
        Return list of all devices in the mesh.
        """
        return list(self.graph.nodes)

    def get_device_info(self, device_id: str) -> Dict[str, Any]:
        """
        Return metadata stored for a device.
        """
        return self.device_info.get(device_id, {})

    def calculate_network_stats(self) -> Dict[str, Any]:
        """
        Return basic statistics about the mesh network.
        """
        if self.graph.number_of_nodes() == 0:
            return {"nodes": 0, "edges": 0, "diameter": 0}
        try:
            diameter = nx.diameter(self.graph)
        except:
            diameter = -1
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "diameter": diameter,
            "density": nx.density(self.graph)
        }

    def clear(self) -> None:
        """
        Clear all devices and connections.
        """
        self.graph.clear()
        self.device_info.clear()
        logger.info("Mesh network cleared")