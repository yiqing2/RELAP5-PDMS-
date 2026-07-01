"""Undirected graph data structure for piping network topology.

Uses an adjacency list representation. Vertices are connection point IDs;
edges store the component object connecting two vertices.
"""

from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Optional


class UndirectedGraph:
    """Undirected graph using adjacency list representation.

    Vertices are ConnectionPoint.original_id strings.
    Edges are component instances keyed by (u, v) tuple (u < v).
    """

    def __init__(self):
        self._adj: Dict[str, Set[str]] = defaultdict(set)
        self._edges: Dict[Tuple[str, str], object] = {}
        self._vertices: Set[str] = set()
        self._id_map: Dict[str, int] = {}
        self._rev_map: Dict[int, str] = {}

    # ------------------------------------------------------------------
    # Edge / vertex management
    # ------------------------------------------------------------------

    def add_edge(self, u: str, v: str, component: object) -> None:
        """Add an undirected edge between u and v, storing the component."""
        ...

    def get_neighbors(self, vertex: str) -> Set[str]:
        """Return the set of neighbor vertex IDs."""
        ...

    def get_edge_component(self, u: str, v: str) -> Optional[object]:
        """Return the component stored on edge (u, v), or None."""
        ...

    def get_degree(self, vertex: str) -> int:
        """Return the degree of a vertex."""
        ...

    def find_dangling_vertices(self) -> List[str]:
        """Return vertices with degree == 1 (potential boundaries)."""
        ...

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def vertices(self) -> Set[str]:
        """All vertex IDs in the graph."""
        return self._vertices

    @property
    def edges(self) -> Dict[Tuple[str, str], object]:
        """All edges as (u, v) -> component mapping."""
        return self._edges

    # ------------------------------------------------------------------
    # Traversal and numbering
    # ------------------------------------------------------------------

    def bfs_numbering(self, start: Optional[str] = None) -> Dict[str, int]:
        """BFS traversal assigning unique 1-based integer IDs.

        If start is None, begins from a dangling vertex if available.
        Handles disconnected components.
        """
        ...

    def dfs_numbering(self, start: Optional[str] = None) -> Dict[str, int]:
        """DFS traversal assigning unique 1-based integer IDs.

        If start is None, begins from a dangling vertex if available.
        Handles disconnected components.
        """
        ...

    # ------------------------------------------------------------------
    # Mapping accessors
    # ------------------------------------------------------------------

    def get_id_map(self) -> Dict[str, int]:
        """Return original_id -> mapped_id dictionary."""
        return self._id_map

    def get_reverse_map(self) -> Dict[int, str]:
        """Return mapped_id -> original_id dictionary."""
        return self._rev_map
