"""Module 3: Boundary condition injection.

Reads a boundary.csv configuration file and/or auto-detects dangling
vertices (degree == 1) as boundary condition candidates for RELAP5.
"""

from typing import Dict, Set, Optional
from src.models.component import BoundaryType
from src.models.graph import UndirectedGraph


class BoundaryConfig:
    """Manages boundary condition assignment for connection points.

    Two sources of boundary information:
      1. Explicit configuration from boundary.csv
      2. Auto-detection of dangling vertices (degree == 1)

    boundary.csv format:
        original_id, boundary_type
        CONN_A, P
        CONN_B, T
    """

    def __init__(self, graph: UndirectedGraph):
        """Initialize with a reference to the topology graph."""
        ...

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_config(self, filepath: Optional[str] = None) -> None:
        """Load boundary configuration from a CSV file.

        Args:
            filepath: Path to boundary.csv. If None, skips loading.

        Raises:
            ValueError: If an unknown boundary type is encountered.
        """
        ...

    def auto_detect_dangling(self) -> Set[str]:
        """Auto-detect dangling vertices as default pressure boundaries.

        A dangling vertex has degree == 1 (appears in exactly one component).

        Returns:
            Set of original_id strings that were auto-detected.
        """
        ...

    def is_boundary(self, original_id: str) -> bool:
        """Check whether a connection point is marked as a boundary."""
        ...

    def get_boundary_type(self, original_id: str) -> BoundaryType:
        """Get the boundary type for a connection point.

        Defaults to PRESSURE if not explicitly configured.
        """
        ...
