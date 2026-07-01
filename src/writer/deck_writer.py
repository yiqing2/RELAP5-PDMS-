"""Module 4: RELAP5 deck writer — main orchestrator.

Assembles the complete RELAP5 input deck by:
  1. Writing header, time-step, and trip cards.
  2. Allocating card numbers for each component type.
  3. Delegating to per-card-type writers in topological order.
  4. Writing the end-of-file trailer.
"""

from typing import List, Dict, Optional
from src.models.graph import UndirectedGraph
from src.models.component import ConnectionPoint, PipeComponent, ValveComponent, JunctionComponent
from src.boundary.boundary_config import BoundaryConfig


class DeckWriter:
    """Orchestrates the generation of a complete RELAP5 input deck.

    Card numbering ranges (configurable):
        TMDPVOL: 200+
        SNGLJUN: 300+
        PIPE:    400+
        VALVE:   500+
    """

    def __init__(self,
                 graph: UndirectedGraph,
                 boundary_config: BoundaryConfig,
                 bdry_start: int = 200,
                 sngljun_start: int = 300,
                 pipe_start: int = 400,
                 valve_start: int = 500):
        """Initialize the deck writer.

        Args:
            graph: The topology graph with ID mappings.
            boundary_config: Configured boundary conditions.
            bdry_start: Starting card number for TMDPVOL boundaries.
            sngljun_start: Starting card number for SNGLJUN cards.
            pipe_start: Starting card number for PIPE cards.
            valve_start: Starting card number for VALVE cards.
        """
        ...

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def write_deck(self, output_path: str) -> None:
        """Generate the complete RELAP5 input deck file.

        Writes header, time-step cards, trip cards, hydrodynamic components,
        and the '. end of input data' trailer.

        Args:
            output_path: Path to the output relap5_deck.txt file.
        """
        ...

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _prepare_component_order(self) -> None:
        """Sort components by graph traversal order for sequential output."""
        ...

    def _allocate_card(self, comp_type_or_obj) -> int:
        """Allocate and return the next card number for a component type."""
        ...

    def _get_connection_point(self, orig_id: str) -> Optional[ConnectionPoint]:
        """Retrieve a ConnectionPoint by its original_id."""
        ...
