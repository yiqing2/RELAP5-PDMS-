# -*- coding: utf-8 -*-
"""RELAP5 input deck parser."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class R5Component:
    card_id: int = 0
    name: str = ""
    comp_type: str = ""
    from_addr: str = ""
    to_addr: str = ""
    volume_count: int = 1
    flow_area: float = 0.0
    length: float = 0.0
    diameter: float = 0.0
    valve_type: str = ""


def parse_relap5_deck(filepath: str) -> Dict[int, R5Component]:
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    components: Dict[int, R5Component] = {}
    current_id: Optional[int] = None

    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line or line.startswith("*") or line.startswith("."):
            continue

        parts = line.split()
        if not parts:
            continue

        # Check for component header: CCC0000 NAME TYPE
        cid = _try_component_header(parts)
        if cid is not None:
            comp_type = _normalize_type(parts[-1])
            name = parts[-2] if len(parts) >= 3 else parts[-1]
            components[cid] = R5Component(
                card_id=cid, name=name, comp_type=comp_type,
            )
            current_id = cid
            continue

        if current_id is None or current_id not in components:
            continue

        comp = components[current_id]

        # Parse card group from first token
        token = parts[0]
        if not (len(token) in (7, 8) and token.isdigit()):
            continue

        cg = _card_group(token)

        # SNGLJUN connections
        if comp.comp_type == "sngljun" and cg == "0101":
            if len(parts) >= 2: comp.from_addr = parts[1]
            if len(parts) >= 3: comp.to_addr = parts[2]
            if len(parts) >= 4: comp.flow_area = _float(parts[3])

        # VALVE connections
        elif comp.comp_type == "valve" and cg == "0101":
            if len(parts) >= 2: comp.from_addr = parts[1]
            if len(parts) >= 3: comp.to_addr = parts[2]
            if len(parts) >= 4: comp.flow_area = _float(parts[3])

        # VALVE type
        elif comp.comp_type == "valve" and cg == "0300":
            if len(parts) >= 2: comp.valve_type = parts[1]

        # TMDPVOL geometry
        elif comp.comp_type == "tmdpvol" and cg == "0101":
            if len(parts) >= 2: comp.flow_area = _float(parts[1])
            if len(parts) >= 3: comp.length = _float(parts[2])

        elif comp.comp_type == "tmdpvol" and cg in ("0102", "0103"):
            if len(parts) >= 3: comp.diameter = _float(parts[2])

        # PIPE geometry
        elif comp.comp_type == "pipe" and cg == "0001":
            comp.volume_count = int(parts[1])

        elif comp.comp_type == "pipe" and cg == "0101":
            if len(parts) >= 2: comp.flow_area = _float(parts[1])

        elif comp.comp_type == "pipe" and cg == "0301":
            if len(parts) >= 2: comp.length = _float(parts[1])

        elif comp.comp_type == "pipe" and cg == "0801":
            if len(parts) >= 3: comp.diameter = _float(parts[2])

    return components


def _try_component_header(parts: list) -> Optional[int]:
    """Check if this is a component header line: CCC0000 NAME TYPE."""
    if len(parts) < 2:
        return None
    token = parts[0]
    if not (len(token) == 7 and token.isdigit()):
        return None
    if not token.endswith("0000"):
        return None
    comp_type = _normalize_type(parts[-1])
    if comp_type in ("tmdpvol", "sngljun", "pipe", "valve"):
        return int(token[:3])
    return None


def _card_group(token: str) -> str:
    """Extract XXNN from CCCXXNNN or CCCXXNN."""
    if len(token) >= 5:
        return token[3:7]
    return ""


def _normalize_type(t: str) -> str:
    t = t.lower()
    if "tmdp" in t: return "tmdpvol"
    if "sngl" in t: return "sngljun"
    if "pipe" in t: return "pipe"
    if "valv" in t or "mtrvlv" in t: return "valve"
    return t


def _float(s: str) -> float:
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_relap5_addr(addr: str) -> Tuple[int, int]:
    """Parse a RELAP5 address string into (comp_id, volume_idx).

    Address format: CCCXXNNNN or CCCXXNNN
      CCC  = component card ID (3 digits)
      XX   = card group (2 digits, e.g. 01=vol geometry, 07=vol geometry)
      NNNN = volume/junction index (last 2-4 digits)

    Examples:
        "202070002" -> (202, 2)   # PIPE-202, volume 2
        "200010000" -> (200, 0)   # TMDPVOL-200 (boundary)
        "206040001" -> (206, 1)   # PIPE-206, volume 1
        "310040002" -> (310, 2)   # PIPE-310, volume 2
    """
    if not addr or len(addr) < 7:
        return (0, 0)
    try:
        comp_id = int(addr[:3])
        # The volume index is the last 2-4 digits (after the card group)
        # Card group is digits 4-5 (0-indexed: indices 3-4)
        # Volume index is everything after position 5
        vol_str = addr[5:]
        vol_idx = int(vol_str) if vol_str else 0
        return (comp_id, vol_idx)
    except (ValueError, IndexError):
        return (0, 0)


def build_topology_order(components: Dict[int, R5Component]) -> List[int]:
    """Topological sort: main flow path first, then branches."""
    if not components:
        return []

    adj: Dict[int, List[int]] = {cid: [] for cid in components}
    for cid, comp in components.items():
        for addr in (comp.from_addr, comp.to_addr):
            if addr and len(addr) >= 3 and addr[:3].isdigit():
                neighbor = int(addr[:3])
                if neighbor in adj and neighbor != cid:
                    adj[cid].append(neighbor)

    # Deduplicate
    for k in adj:
        adj[k] = list(dict.fromkeys(adj[k]))

    # BFS from first TMDPVOL boundary
    boundaries = sorted([cid for cid, c in components.items()
                         if c.comp_type == "tmdpvol"])
    if boundaries:
        start = boundaries[0]
    elif components:
        start = min(components.keys())
    else:
        return []

    visited = set()
    order = []
    queue = [start]
    while queue:
        node = queue.pop(0)
        if node in visited:
            continue
        visited.add(node)
        order.append(node)
        for nb in adj.get(node, []):
            if nb not in visited:
                queue.append(nb)

    for cid in sorted(components.keys()):
        if cid not in visited:
            order.append(cid)

    return order
