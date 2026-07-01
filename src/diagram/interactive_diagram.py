"""Module 5c: Interactive HTML diagram (optional, requires plotly).

Generates an interactive HTML diagram with:
  - Zoom and pan
  - Hover tooltips showing component details (name, type, diameter, length)
  - Click-to-highlight connected nodes
  - Search box for finding components by name
  - Export to PNG button

Usage:
    pip install plotly
    python main.py pdms_export.txt --interactive
"""

from typing import Dict
from src.models.graph import UndirectedGraph


class InteractiveDiagramGenerator:
    """Generates an interactive plotly-based HTML diagram.

    This is an optional feature requiring plotly to be installed.
    """

    def __init__(self, graph: UndirectedGraph,
                 id_map: Dict[str, int],
                 boundary_set: set):
        """Initialize the interactive diagram generator.

        Args:
            graph: The undirected topology graph.
            id_map: original_id -> mapped_id dictionary.
            boundary_set: Set of original_ids marked as boundaries.
        """
        ...

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, output_path: str,
                 title: str = "Piping Network Topology (Interactive)") -> None:
        """Generate and save the interactive HTML diagram.

        Args:
            output_path: Output file path (.html).
            title: Diagram title.
        """
        ...
