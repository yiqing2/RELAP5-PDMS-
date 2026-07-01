"""SNGLJUN card writer.

Generates RELAP5 single junction cards for connecting components.

Card layout:
  CCC0000  junCCC  sngljun
  CCC0101  FROM_ADDR  TO_ADDR  AREA  AF  AR  FLAGS
  CCC0201  1  0.0  0.0000  0.0
"""

from typing import Dict, TextIO
from src.models.component import JunctionComponent
from src.boundary.boundary_config import BoundaryConfig


def write_sngljun_card(f: TextIO, card_num: int, junc: JunctionComponent,
                       id_map: Dict[str, int],
                       component_card_map: Dict[str, int],
                       boundary_config: BoundaryConfig) -> None:
    """Write a complete SNGLJUN card group to the open file handle.

    Args:
        f: Open file handle for writing.
        card_num: Assigned 3-digit component number (CCC).
        junc: The JunctionComponent to write.
        id_map: original_id -> mapped_id dictionary.
        component_card_map: component name -> CCC number mapping.
        boundary_config: Boundary condition configuration.
    """
    ...
