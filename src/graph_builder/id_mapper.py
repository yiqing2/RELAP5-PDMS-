"""Module 2b: ID mapping via BFS/DFS graph traversal.

Assigns unique integer IDs to every connection point (graph vertex)
and writes the mapping log for manual review.
"""

from typing import Dict
from src.models.graph import UndirectedGraph


class IDMapper:
    """Assigns unique 1-based integer IDs to graph vertices via traversal.

    Supports both BFS (default, follows physical layout) and DFS numbering.
    """

    def __init__(self, graph: UndirectedGraph, method: str = "bfs"):
        """Initialize with a graph and traversal method.

        Args:
            graph: The undirected topology graph.
            method: "bfs" (default) or "dfs".
        """
        ...

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assign_ids(self) -> Dict[str, int]:
        """Execute the traversal and return original_id -> mapped_id dict."""
        ...

    def write_mapping_log(self, filepath: str) -> None:
        """Write the ID mapping to a CSV file for manual review.

        Output columns: original_id, mapped_id
        """
        ...
