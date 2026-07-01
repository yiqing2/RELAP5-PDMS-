"""PDMS component data models.

Defines the core data structures representing piping components
parsed from PDMS export files.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ComponentType(Enum):
    """Types of hydrodynamic components in the piping network."""
    PIPE = "PIPE"
    VALVE = "VALVE"
    JUNC = "JUNC"          # tee, elbow, cross — pure junction nodes
    BOUNDARY = "BOUNDARY"  # TMDPVOL boundary condition


class BoundaryType(Enum):
    """RELAP5 boundary condition types."""
    PRESSURE = "P"
    TEMPERATURE = "T"
    FLOW = "F"


@dataclass
class Point3D:
    """A 3D coordinate from the PDMS model."""
    x: float
    y: float
    z: float


@dataclass
class ConnectionPoint:
    """A connection endpoint on a PDMS component.

    In the undirected graph, connection points become vertices.
    """
    original_id: str                      # Raw PDMS identifier
    mapped_id: int = -1                   # Assigned after BFS/DFS traversal
    coordinate: Optional[Point3D] = None
    is_boundary: bool = False
    boundary_type: Optional[BoundaryType] = None


@dataclass
class PipeComponent:
    """Represents a PIPE element from PDMS."""
    name: str
    conn1: ConnectionPoint
    conn2: ConnectionPoint
    roughness: float
    diameter: float
    length: float
    volume_count: int = 1


@dataclass
class ValveComponent:
    """Represents a VALVE element from PDMS."""
    name: str
    conn1: ConnectionPoint
    conn2: ConnectionPoint
    roughness: float
    diameter: float
    valve_type: str = "mtrvlv"
    open_trip: int = 402
    close_trip: int = 403
    change_rate: float = 3.33333
    initial_position: float = 1.0


@dataclass
class JunctionComponent:
    """Represents a tee, elbow, or other pure junction node."""
    name: str
    conn1: ConnectionPoint
    conn2: ConnectionPoint
    diameter: float
    flow_area: Optional[float] = None
