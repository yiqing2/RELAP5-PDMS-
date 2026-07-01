"""TMDPVOL card writer.

Generates RELAP5 time-dependent volume cards for boundary conditions.

Card layout:
  CCC0000  NAME  tmdpvol
  CCC0101  FLOW_AREA  LENGTH  0.0  0.0  0.0  0.0
  CCC0102  ROUGHNESS  0.0  FLAGS      (or 0103 variant)
  CCC0200  3
  CCC0201  0.0  8.0e6  420.75
"""

from typing import TextIO
from src.models.component import ConnectionPoint, BoundaryType


def write_tmdpvol_card(f: TextIO, card_num: int,
                       conn: ConnectionPoint,
                       btype: BoundaryType) -> None:
    """Write a complete TMDPVOL boundary condition card group.

    Args:
        f: Open file handle for writing.
        card_num: Assigned 3-digit component number (CCC).
        conn: The connection point marked as boundary.
        btype: Boundary condition type (P, T, or F).
    """
    ...
