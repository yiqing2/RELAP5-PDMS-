"""Module 5a: Static network topology diagram.

Generates a PNG/SVG diagram of the piping network showing:
  - Nodes (connection points) labeled with mapped integer IDs
  - Edges (components) color-coded by type (blue=PIPE, red=VLV, green=JUNC)
  - Boundary nodes highlighted as orange diamonds
  - Legend
"""

from typing import Dict, Set, Tuple
from src.models.graph import UndirectedGraph


# Color scheme for component types
COMPONENT_COLORS = {
    "PIPE":     "#2196F3",   # blue
    "VALVE":    "#F44336",   # red
    "JUNC":     "#4CAF50",   # green
    "BOUNDARY": "#FF9800",   # orange
}


class TopologyDiagramGenerator:
    """Generates a static network topology diagram.

    Uses networkx for graph layout (Kamada-Kawai default) and
    matplotlib for rendering.
    """

    def __init__(self, graph: UndirectedGraph,
                 id_map: Dict[str, int],
                 boundary_set: set,
                 layout: str = "kamada_kawai"):
        """Initialize the topology diagram generator.

        Args:
            graph: The undirected topology graph.
            id_map: original_id -> mapped_id dictionary.
            boundary_set: Set of original_ids marked as boundaries.
            layout: Layout algorithm name
                    ("kamada_kawai", "spring", "shell", "spectral").
        """
        ...

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, output_path: str,
                 title: str = "Piping Network Topology",
                 figsize: Tuple[int, int] = (16, 12),
                 dpi: int = 150) -> None:
        """Generate and save the topology diagram.

        Args:
            output_path: Output file path (.png or .svg).
            title: Diagram title.
            figsize: Figure size in inches (width, height).
            dpi: Output resolution.
        """
        ...

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_networkx_graph(self) -> None:
        """Convert internal UndirectedGraph to a networkx graph with metadata."""
        ...

    def _get_layout(self):
        """Compute node positions using the selected layout algorithm."""
        ...

    @staticmethod
    def _get_component_type(comp) -> str:
        """Determine the component type string from a component object."""
        ...
