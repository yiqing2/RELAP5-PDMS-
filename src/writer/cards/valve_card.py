"""VALVE card writer.

Generates RELAP5 VALVE (mtrvlv) component cards matching break.i format.

Card layout:
  CCC0000  junCCC  valve
  CCC0101  FROM_ADDR  TO_ADDR  AREA  AF  AR  FLAGS
  CCC0201  1  0.0  0.0000  0.0
  CCC0300  mtrvlv
  CCC0301  CLOSE_TRIP  OPEN_TRIP  CHANGE_RATE  INIT_POS
  CCC0400  0.0  0.0
  CCC0401  1.0  PARAM2  PARAM3
"""

from typing import Dict, TextIO
from src.models.component import ValveComponent


def write_valve_card(f: TextIO, card_num: int, valve: ValveComponent,
                     id_map: Dict[str, int],
                     component_card_map: Dict[str, int]) -> None:
    """Write a complete VALVE card group to the open file handle.

    Args:
        f: Open file handle for writing.
        card_num: Assigned 3-digit component number (CCC).
        valve: The ValveComponent to write.
        id_map: original_id -> mapped_id dictionary.
        component_card_map: component name -> CCC number mapping.
    """
    ...
