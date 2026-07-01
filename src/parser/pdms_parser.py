"""Module 1: PDMS export file parser.

Parses a CSV-like PDMS export into a list of component objects
(PipeComponent, ValveComponent, JunctionComponent).
"""

from typing import List
from src.models.component import ComponentType


class PDMSParseError(Exception):
    """Raised when PDMS export data is malformed or missing required fields."""
    pass


class PDMSParser:
    """Parses a PDMS export text file into component objects.

    Expected columns (CSV, no header):
        name, conn1_id, conn2_id, x1, y1, z1, x2, y2, z2,
        roughness, diameter, length, [type_override]

    If type_override is absent, component type is inferred from
    the component name via keyword matching.
    """

    REQUIRED_COLUMNS = 12
    TYPE_COLUMN_INDEX = 12  # optional 13th column (0-indexed)

    def __init__(self, filepath: str):
        """Initialize the parser with a path to the PDMS export file."""
        ...

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self) -> List[object]:
        """Parse the PDMS export file and return a list of components.

        Returns:
            List of PipeComponent, ValveComponent, or JunctionComponent.

        Raises:
            PDMSParseError: If required data is missing or malformed.
        """
        ...

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_row(self, row: List[str], line_no: int) -> object:
        """Parse a single CSV row into the appropriate component object."""
        ...

    def _infer_type(self, name: str, row: List[str],
                    line_no: int) -> ComponentType:
        """Infer component type from name keywords or explicit type column."""
        ...

    def _validate_coordinates(self) -> None:
        """Ensure every component has valid coordinates on both endpoints.

        Raises:
            PDMSParseError: If any coordinate is missing.
        """
        ...
