"""Module 2a: Topology graph construction.

Builds an UndirectedGraph from a list of parsed PDMS components.
Each component becomes an undirected edge between its two connection points.
"""

from typing import List
from src.models.graph import UndirectedGraph
from src.models.component import ConnectionPoint


class TopologyBuilder:
    """Builds an undirected graph from parsed PDMS components.

    Each component (PIPE, VALVE, JUNC) becomes an edge between its
    two connection points. Duplicate connections are detected and warned.
    """

    def __init__(self):
        """Initialize an empty topology builder."""
        ...

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self, components: List[object]) -> UndirectedGraph:
        """Construct the undirected graph from a list of components.

        Detects and logs duplicate connections.

        Args:
            components: List of PipeComponent, ValveComponent, JunctionComponent.

        Returns:
            The constructed UndirectedGraph.
        """
        ...

    def get_connection_point(self, original_id: str) -> ConnectionPoint:
        """Look up a ConnectionPoint object by its original_id."""
        ...
