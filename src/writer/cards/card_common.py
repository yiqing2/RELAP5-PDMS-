"""Shared utilities for RELAP5 card generation.

Includes flow direction assignment by coordinate comparison
and card/volume addressing format helpers.
"""

from typing import Tuple
from src.models.component import Point3D


def assign_flow_direction(coord1: Point3D, coord2: Point3D) -> Tuple[str, str]:
    """Assign reference flow direction by coordinate sorting.

    Compares two 3D coordinates and returns (inlet_label, outlet_label).
    Priority: X > Y > Z (ascending: smaller coordinate = inlet).

    Args:
        coord1: First endpoint coordinate.
        coord2: Second endpoint coordinate.

    Returns:
        Tuple of ("inlet" | "outlet", "inlet" | "outlet") where the
        first element corresponds to coord1's role.

    Raises:
        ValueError: If either coordinate is None.
    """
    ...


def format_volume_address(comp_num: int, vol_num: int,
                          sub_idx: int = 0) -> str:
    """Format a RELAP5 volume address: CCCVVSSSS.

    Args:
        comp_num: 3-digit component number (e.g. 202).
        vol_num: 2-digit volume number within the component.
        sub_idx: 4-digit sub-index (default 0).

    Returns:
        Formatted address string like "202010000".
    """
    ...


def format_card_number(comp_num: int, card_group: int, seq: int) -> str:
    """Format a RELAP5 card number: CCCXXNNN.

    Args:
        comp_num: 3-digit component number.
        card_group: 2-digit card group (00=header, 01=geometry, etc.).
        seq: 3-digit sequence number (volume or junction number).

    Returns:
        Formatted card number string like "2020101".
    """
    ...
