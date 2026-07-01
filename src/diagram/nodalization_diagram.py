# -*- coding: utf-8 -*-
"""Nodalization diagram generator v5 — engineering schematic style.

Produces professional engineering nodalization diagrams from RELAP5
input deck data, with hierarchical layout, volume cell display,
orthogonal connection routing, and engineering-standard symbols.

Architecture:
  1. Topology analysis  — parse addresses, build connection graph,
                          identify main path and branch tap points
  2. Layout assignment   — hierarchical (x, y) positioning
  3. Component rendering — TMDPVOL, PIPE, VALVE, SNGLJUN renderers
  4. Connection routing  — orthogonal polyline connections + arrows
"""

from __future__ import annotations

import os
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import (Circle, FancyBboxPatch, Polygon)

from src.parser.relap5_parser import R5Component, parse_relap5_addr

# =========================================================================
# Color & style constants
# =========================================================================

EDGE_COLOR       = "#1a1a1a"
BOUNDARY_FILL    = "#D6EAF8"
PIPE_FILL        = "#FFFFFF"
VALVE_FILL       = "#FFFFFF"
JUNCTION_FILL    = "#333333"
CELL_PARTITION   = "#CCCCCC"
MAIN_LINE_COLOR  = "#1a1a1a"
BRANCH_LINE_COLOR = "#555555"
RETURN_LINE_COLOR = "#999999"
BG_COLOR         = "#FFFFFF"
FONT_FAMILY      = "sans-serif"

# Component geometry — uniform sizing
TMDPVOL_W = 1.8
TMDPVOL_H = 1.4
PIPE_H    = 1.2
PIPE_MIN_W = 1.8
PIPE_MAX_W = 3.5
PIPE_W_PER_VOL = 0.22
VALVE_W   = 1.4
VALVE_H   = 0.7
JUNC_R    = 0.18
JUNC_W    = 0.50

ROW_SPACING      = 5.5
MAIN_ROW_Y       = 0.0
H_GAP             = 0.70
B_H_GAP           = 0.40          # tighter gap on branch rows
DROP_MIN          = 2.5           # vertical drop before turning — halfway between rows

# =========================================================================
# Data classes for topology analysis
# =========================================================================

@dataclass
class ConnPoint:
    """A precise connection point on a component."""
    comp_id: int
    volume_idx: int          # 0 = boundary; >=1 = volume index within component


@dataclass
class ConnEdge:
    """A directed edge between two connection points via a junction component."""
    from_cp: ConnPoint
    to_cp: ConnPoint
    via_comp_id: int         # the SNGLJUN/VALVE that bridges them


@dataclass
class BranchInfo:
    """Information about one branch subgraph."""
    comp_ids: List[int]                        # ordered component IDs along branch
    tap_from: ConnPoint                        # where it taps from the main path
    tap_to: Optional[ConnPoint] = None         # where it returns (None = dead-end)
    row_index: int = 0                         # vertical layer


@dataclass
class LayoutPlan:
    """Complete layout plan for the diagram."""
    main_path: List[int] = field(default_factory=list)
    branches: List[BranchInfo] = field(default_factory=list)
    branch_comp_ids: Set[int] = field(default_factory=set)
    positions: Dict[int, Tuple[float, float, str]] = field(default_factory=dict)
    # (x_center, y_center, row_label)


# =========================================================================
# Phase 1a: Address parsing
# =========================================================================

def _parse_addr(addr: str) -> ConnPoint:
    """Parse a RELAP5 address string into a ConnPoint."""
    comp_id, vol_idx = parse_relap5_addr(addr)
    return ConnPoint(comp_id=comp_id, volume_idx=vol_idx)


# =========================================================================
# Phase 1b: Connection graph construction
# =========================================================================

def _build_component_adjacency(
    components: Dict[int, R5Component]
) -> Dict[int, List[int]]:
    """Build undirected component-level adjacency list.

    Uses from_addr / to_addr on SNGLJUN and VALVE components to
    establish which components are connected.
    """
    adj: Dict[int, List[int]] = defaultdict(list)

    for cid, comp in components.items():
        if comp.comp_type in ("sngljun", "valve"):
            if comp.from_addr:
                nbr = _parse_addr(comp.from_addr).comp_id
                if nbr and nbr in components and nbr != cid:
                    adj[cid].append(nbr)
                    adj[nbr].append(cid)
            if comp.to_addr:
                nbr = _parse_addr(comp.to_addr).comp_id
                if nbr and nbr in components and nbr != cid:
                    adj[cid].append(nbr)
                    adj[nbr].append(cid)

    # Deduplicate
    for k in adj:
        adj[k] = list(dict.fromkeys(adj[k]))

    return adj


# =========================================================================
# Phase 1c: Topology analysis — main path + branch detection
# =========================================================================

def _bfs_path(
    adj: Dict[int, List[int]], start: int, end: int
) -> List[int]:
    """BFS shortest path (fallback)."""
    if start == end:
        return [start]
    visited = {start}
    parent: Dict[int, int] = {}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for nbr in adj.get(node, []):
            if nbr not in visited:
                visited.add(nbr)
                parent[nbr] = node
                if nbr == end:
                    # Reconstruct path
                    path = [end]
                    while path[-1] != start:
                        path.append(parent[path[-1]])
                    path.reverse()
                    return path
                queue.append(nbr)
    return []


def analyze_topology(
    components: Dict[int, R5Component]
) -> LayoutPlan:
    """Analyze the component topology and produce a LayoutPlan.

    Steps:
      1. Build component adjacency
      2. Find TMDPVOL boundaries
      3. Find longest path between boundaries → main path
      4. Detect branch subgraphs and their tap points
    """
    plan = LayoutPlan()

    if not components:
        return plan

    adj = _build_component_adjacency(components)

    # Find TMDPVOL boundaries
    boundaries = sorted([
        cid for cid, c in components.items() if c.comp_type == "tmdpvol"
    ])

    # Set of PIPE component IDs for path scoring
    pipe_ids = {cid for cid, c in components.items() if c.comp_type == "pipe"}

    # --- Determine main path ---
    if len(boundaries) >= 2:
        # Use shortest path (BFS) between first and last boundary.
        # The main flow path is the most DIRECT route between inlet/outlet.
        main_path = _bfs_path(adj, boundaries[0], boundaries[-1])
    elif len(boundaries) == 1:
        # One boundary — BFS from it, then DFS to a dangling endpoint
        main_path = _bfs_find_main_from_single_boundary(adj, boundaries[0])
    else:
        # No boundaries — find longest path between any degree-1 nodes
        deg1 = [cid for cid, nbrs in adj.items() if len(nbrs) == 1]
        if len(deg1) >= 2:
            main_path = _find_longest_path(adj, deg1[0], deg1[-1], pipe_ids)
        elif components:
            # Arbitrary start
            start = min(components.keys())
            main_path = _bfs_find_main_from_single_boundary(adj, start)
        else:
            main_path = []

    if not main_path and components:
        main_path = [min(components.keys())]

    plan.main_path = main_path
    main_set = set(main_path)

    # --- Detect branches ---
    # Components not on the main path that are connected to it
    remaining = set(components.keys()) - main_set
    visited_branch: Set[int] = set()
    row_idx = 1

    for cid in list(remaining):
        if cid in visited_branch:
            continue
        # Find the subgraph containing this component
        subgraph = _collect_branch_subgraph(cid, adj, main_set, remaining)
        visited_branch.update(subgraph)
        if not subgraph:
            continue

        # Find tap points — where this subgraph connects to the main path
        tap_from, tap_to = _find_tap_points(subgraph, adj, main_set, components)

        # Determine branch order by BFS walk from tap_from
        ordered = _order_branch(subgraph, adj, tap_from.comp_id if tap_from else None)

        branch = BranchInfo(
            comp_ids=ordered,
            tap_from=tap_from,
            tap_to=tap_to,
            row_index=row_idx,
        )
        plan.branches.append(branch)
        plan.branch_comp_ids.update(subgraph)
        row_idx += 1

    return plan


def _bfs_find_main_from_single_boundary(
    adj: Dict[int, List[int]], start: int
) -> List[int]:
    """BFS from a single boundary to find a long path."""
    # Find the farthest node from start via BFS
    visited: Set[int] = set()
    queue = deque([start])
    visited.add(start)
    farthest = start
    while queue:
        node = queue.popleft()
        farthest = node
        for nbr in adj.get(node, []):
            if nbr not in visited:
                visited.add(nbr)
                queue.append(nbr)
    # Now find path from start to farthest
    return _bfs_path(adj, start, farthest)


def _collect_branch_subgraph(
    seed: int,
    adj: Dict[int, List[int]],
    main_set: Set[int],
    remaining: Set[int],
) -> Set[int]:
    """Collect a connected subgraph of non-main-path components via BFS."""
    subgraph: Set[int] = set()
    queue = deque([seed])
    while queue:
        node = queue.popleft()
        if node in subgraph or node in main_set:
            continue
        if node not in remaining:
            continue
        subgraph.add(node)
        for nbr in adj.get(node, []):
            if nbr not in subgraph and nbr not in main_set:
                queue.append(nbr)
    return subgraph


def _find_tap_points(
    subgraph: Set[int],
    adj: Dict[int, List[int]],
    main_set: Set[int],
    components: Dict[int, R5Component],
) -> Tuple[Optional[ConnPoint], Optional[ConnPoint]]:
    """Find where a branch subgraph connects to the main path.

    Returns (tap_from, tap_to) — the main-path connection points.
    tap_to may be None for dead-end branches.
    """
    tap_connections: List[Tuple[int, int, str, str]] = []
    # (branch_comp_id, main_comp_id, branch_addr, main_comp_addr)

    for bid in subgraph:
        comp = components.get(bid)
        if comp is None:
            continue
        if comp.comp_type not in ("sngljun", "valve"):
            continue
        # Check from_addr
        if comp.from_addr:
            cp = _parse_addr(comp.from_addr)
            if cp.comp_id in main_set:
                tap_connections.append((bid, cp.comp_id, comp.from_addr, ""))
        # Check to_addr
        if comp.to_addr:
            cp = _parse_addr(comp.to_addr)
            if cp.comp_id in main_set:
                tap_connections.append((bid, cp.comp_id, comp.to_addr, ""))

    tap_from = None
    tap_to = None
    for bid, main_cid, addr, _ in tap_connections:
        cp = _parse_addr(addr)
        if tap_from is None:
            tap_from = cp
        elif tap_to is None:
            tap_to = cp

    return tap_from, tap_to


def _order_branch(
    subgraph: Set[int],
    adj: Dict[int, List[int]],
    start: Optional[int],
) -> List[int]:
    """Order branch components by walking from the start point."""
    if not subgraph:
        return []
    if start is None or start not in subgraph:
        start = min(subgraph)

    visited: Set[int] = set()
    order: List[int] = []
    queue = deque([start])

    # Build subgraph-only adjacency
    sub_adj: Dict[int, List[int]] = {}
    for cid in subgraph:
        sub_adj[cid] = [n for n in adj.get(cid, []) if n in subgraph]

    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        order.append(node)
        for nbr in sub_adj.get(node, []):
            if nbr not in visited:
                queue.append(nbr)

    # Add any unvisited
    for cid in sorted(subgraph):
        if cid not in visited:
            order.append(cid)

    return order


# =========================================================================
# Phase 1d: Hierarchical position assignment
# =========================================================================

@dataclass
class _CompBox:
    """Bounding box for a component after layout."""
    cid: int
    x_left: float
    y_bottom: float
    width: float
    height: float
    row_label: str = "main"

    @property
    def x_center(self) -> float:
        return self.x_left + self.width / 2

    @property
    def y_center(self) -> float:
        return self.y_bottom + self.height / 2

    @property
    def x_right(self) -> float:
        return self.x_left + self.width

    @property
    def y_top(self) -> float:
        return self.y_bottom + self.height


def _comp_width(comp: R5Component) -> float:
    """Compute component display width."""
    if comp.comp_type == "tmdpvol":
        return TMDPVOL_W
    if comp.comp_type == "pipe":
        return max(PIPE_MIN_W, min(PIPE_MAX_W, comp.volume_count * PIPE_W_PER_VOL))
    if comp.comp_type == "valve":
        return VALVE_W
    if comp.comp_type == "sngljun":
        return JUNC_W
    return 0.35


def _comp_height(comp: R5Component) -> float:
    """Compute component display height."""
    if comp.comp_type == "tmdpvol":
        return TMDPVOL_H
    if comp.comp_type == "pipe":
        return PIPE_H
    if comp.comp_type == "valve":
        return VALVE_H
    return JUNC_R * 4  # junction height


def assign_positions(
    plan: LayoutPlan,
    components: Dict[int, R5Component],
) -> Dict[int, _CompBox]:
    """Assign (x, y) bounding boxes to every component.

    Main path on row 0 (y = MAIN_ROW_Y), branches on rows below.
    """
    boxes: Dict[int, _CompBox] = {}

    if not plan.main_path:
        return boxes

    # ---- Main path (row 0) ----
    x = 0.5
    for cid in plan.main_path:
        comp = components.get(cid)
        if comp is None:
            continue
        w = _comp_width(comp)
        h = _comp_height(comp)
        y_bottom = MAIN_ROW_Y - h / 2
        boxes[cid] = _CompBox(cid, x, y_bottom, w, h, "main")
        x = x + w + H_GAP

    # ---- Branch rows ----
    for branch in plan.branches:
        if not branch.comp_ids:
            continue
        row_y = MAIN_ROW_Y - ROW_SPACING * branch.row_index

        # Determine the x-range: from tap point to tap point (or figure width)
        tap_x_left = 0.5
        tap_x_right = x  # default: span full figure width

        if branch.tap_from and branch.tap_from.comp_id in boxes:
            main_box = boxes[branch.tap_from.comp_id]
            # Position relative to the specific volume within the pipe
            main_comp = components.get(branch.tap_from.comp_id)
            if main_comp and main_comp.comp_type == "pipe" and main_comp.volume_count > 0:
                vol_frac = (branch.tap_from.volume_idx - 0.5) / main_comp.volume_count
                tap_x_left = main_box.x_left + vol_frac * main_box.width
            else:
                tap_x_left = main_box.x_center

        if branch.tap_to and branch.tap_to.comp_id in boxes:
            main_box = boxes[branch.tap_to.comp_id]
            main_comp = components.get(branch.tap_to.comp_id)
            if main_comp and main_comp.comp_type == "pipe" and main_comp.volume_count > 0:
                vol_frac = (branch.tap_to.volume_idx - 0.5) / main_comp.volume_count
                tap_x_right = main_box.x_left + vol_frac * main_box.width
            else:
                tap_x_right = main_box.x_center

        # Branch components are drawn at 80% scale for compactness
        BRANCH_SCALE = 0.80

        branch_widths = [
            _comp_width(components[cid]) for cid in branch.comp_ids if cid in components
        ]
        total_bw = sum(branch_widths) * BRANCH_SCALE + B_H_GAP * (len(branch_widths) - 1)
        available = tap_x_right - tap_x_left

        # Start branch centered within available space
        bx = tap_x_left + (available - total_bw) / 2

        for cid in branch.comp_ids:
            comp = components.get(cid)
            if comp is None:
                continue
            w = _comp_width(comp) * BRANCH_SCALE
            h = _comp_height(comp) * BRANCH_SCALE
            y_bottom = row_y - h / 2
            boxes[cid] = _CompBox(cid, bx, y_bottom, w, h, f"branch_{branch.row_index}")
            bx = bx + w + B_H_GAP

    return boxes


# =========================================================================
# Phase 2: Component rendering
# =========================================================================

def _draw_tmdpvol(ax, comp: R5Component, box: _CompBox):
    """Draw a TMDPVOL boundary volume as a rounded rectangle with blue fill."""
    rect = FancyBboxPatch(
        (box.x_left, box.y_bottom), box.width, box.height,
        boxstyle=f"round,pad=0.2",
        fc=BOUNDARY_FILL, ec=EDGE_COLOR, lw=2.0, zorder=3,
    )
    ax.add_patch(rect)

    # "B" badge
    badge_r = 0.16
    badge_cx = box.x_right - 0.25
    badge_cy = box.y_top - 0.25
    ax.add_patch(Circle(
        (badge_cx, badge_cy), badge_r,
        fc="#1a5276", ec="#1a5276", lw=0, zorder=5,
    ))
    ax.text(badge_cx, badge_cy, "B", ha="center", va="center",
            fontsize=14, fontweight="bold", color="white",
            fontfamily=FONT_FAMILY, zorder=6)

    # Labels
    ax.text(box.x_center, box.y_center + 0.15,
            f"TMDPVOL-{comp.card_id}",
            ha="center", va="center", fontsize=16, fontweight="bold",
            fontfamily=FONT_FAMILY, zorder=5)
    ax.text(box.x_center, box.y_center - 0.25,
            comp.name,
            ha="center", va="center", fontsize=14, color="#555",
            fontfamily=FONT_FAMILY, zorder=5)


def _draw_pipe(ax, comp: R5Component, box: _CompBox):
    """Draw a PIPE as a simple rounded rectangle with label and volume count."""
    rect = FancyBboxPatch(
        (box.x_left, box.y_bottom), box.width, box.height,
        boxstyle=f"round,pad=0.12",
        fc=PIPE_FILL, ec=EDGE_COLOR, lw=2.0, zorder=3,
    )
    ax.add_patch(rect)

    n_vols = max(1, comp.volume_count)

    # Label inside the box
    ax.text(box.x_center, box.y_center,
            f"PIPE-{comp.card_id}",
            ha="center", va="center", fontsize=16, fontweight="bold",
            fontfamily=FONT_FAMILY, zorder=5)

    # Volume count below
    ax.text(box.x_center, box.y_bottom - 0.22,
            f"{n_vols} vol",
            ha="center", va="top", fontsize=14, color="#555",
            fontfamily=FONT_FAMILY, zorder=5)


def _draw_valve(ax, comp: R5Component, box: _CompBox):
    """Draw a VALVE as a simple bow-tie symbol (two opposing triangles)."""
    mid_x = box.x_center
    mid_y = box.y_center

    # Left triangle — pointing right (base at left, tip at center)
    left_tri = [(box.x_left, box.y_top), (box.x_left, box.y_bottom), (mid_x, mid_y)]
    ax.add_patch(Polygon(left_tri, fc=VALVE_FILL, ec=EDGE_COLOR, lw=2.0, zorder=3))

    # Right triangle — pointing left (base at right, tip at center)
    right_tri = [(box.x_right, box.y_top), (box.x_right, box.y_bottom), (mid_x, mid_y)]
    ax.add_patch(Polygon(right_tri, fc=VALVE_FILL, ec=EDGE_COLOR, lw=2.0, zorder=3))

    # Label below
    ax.text(mid_x, box.y_bottom - 0.30,
            f"VLV-{comp.card_id}",
            ha="center", va="top", fontsize=16, fontweight="bold",
            fontfamily=FONT_FAMILY, zorder=5)


def _draw_sngljun(ax, comp: R5Component, box: _CompBox):
    """Draw a SNGLJUN as a small filled dot."""
    mid_x = box.x_center
    mid_y = box.y_center

    # Filled circle for all junctions
    ax.add_patch(Circle((mid_x, mid_y), JUNC_R,
                        fc=JUNCTION_FILL, ec=EDGE_COLOR, lw=1.0, zorder=4))

    # Label
    ax.text(mid_x, mid_y - JUNC_R - 0.18,
            f"JUN-{comp.card_id}",
            ha="center", va="top", fontsize=14,
            fontfamily=FONT_FAMILY, zorder=5)


def _draw_tap_marker(ax, x: float, y: float, direction: str = "down"):
    """Draw a small triangular tap-point marker.

    Args:
        direction: "down" (branch leaves main) or "up" (branch returns to main)
    """
    size = 0.18
    if direction == "down":
        pts = [(x - size, y), (x + size, y), (x, y - size * 1.5)]
    else:
        pts = [(x - size, y), (x + size, y), (x, y + size * 1.5)]
    ax.add_patch(Polygon(pts, fc=BRANCH_LINE_COLOR, ec=BRANCH_LINE_COLOR,
                         lw=0.5, zorder=6))


# =========================================================================
# Phase 3: Connection routing
# =========================================================================

def _draw_main_connections(ax, plan: LayoutPlan, boxes: Dict[int, _CompBox]):
    """Draw horizontal arrows between consecutive main path components."""
    main = plan.main_path
    for i in range(len(main) - 1):
        cid_a = main[i]
        cid_b = main[i + 1]
        box_a = boxes.get(cid_a)
        box_b = boxes.get(cid_b)
        if box_a is None or box_b is None:
            continue
        ax.annotate("",
                    xy=(box_b.x_left, box_b.y_center),
                    xytext=(box_a.x_right, box_a.y_center),
                    arrowprops=dict(arrowstyle="->", color=MAIN_LINE_COLOR,
                                    lw=2.0, shrinkA=0, shrinkB=0),
                    zorder=1)


def _draw_branch_connections(
    ax,
    plan: LayoutPlan,
    boxes: Dict[int, _CompBox],
    components: Dict[int, R5Component],
):
    """Draw branch drop/return lines and branch-internal connections."""
    for branch in plan.branches:
        if not branch.comp_ids:
            continue

        branch_boxes = {cid: boxes[cid] for cid in branch.comp_ids if cid in boxes}
        if not branch_boxes:
            continue

        # --- Vertical drop from main to first branch component ---
        if branch.tap_from and branch.tap_from.comp_id in boxes:
            main_box = boxes[branch.tap_from.comp_id]
            main_comp = components.get(branch.tap_from.comp_id)

            # Tap x-position on the main pipe
            if main_comp and main_comp.comp_type == "pipe" and main_comp.volume_count > 0:
                vol_frac = (branch.tap_from.volume_idx - 0.5) / main_comp.volume_count
                tap_x = main_box.x_left + vol_frac * main_box.width
            else:
                tap_x = main_box.x_center

            tap_y = main_box.y_bottom  # bottom of main component

            # First branch component
            first_cid = branch.comp_ids[0]
            first_box = boxes.get(first_cid)
            if first_box:
                # Draw tap marker on main pipe
                _draw_tap_marker(ax, tap_x, tap_y, "down")

                # Orthogonal route: down → horizontal → down
                mid_y = tap_y - DROP_MIN
                target_y = first_box.y_top

                if abs(tap_x - first_box.x_center) < 0.1:
                    # Nearly aligned — straight vertical
                    ax.annotate("",
                                xy=(first_box.x_center, target_y),
                                xytext=(tap_x, tap_y),
                                arrowprops=dict(arrowstyle="->",
                                                color=BRANCH_LINE_COLOR, lw=1.5,
                                                shrinkA=0, shrinkB=0,
                                                connectionstyle="arc3,rad=0"),
                                zorder=2)
                else:
                    # Staircase route
                    route_x = [tap_x, tap_x, first_box.x_center, first_box.x_center]
                    route_y = [tap_y, mid_y, mid_y, target_y]
                    ax.plot(route_x, route_y, color=BRANCH_LINE_COLOR, lw=1.5, zorder=2)
                    # Arrow at end
                    ax.annotate("",
                                xy=(route_x[-1], route_y[-1]),
                                xytext=(route_x[-2], route_y[-2]),
                                arrowprops=dict(arrowstyle="->",
                                                color=BRANCH_LINE_COLOR, lw=1.5,
                                                shrinkA=0, shrinkB=0),
                                zorder=2)

        # --- Branch-internal horizontal connections ---
        for i in range(len(branch.comp_ids) - 1):
            cid_a = branch.comp_ids[i]
            cid_b = branch.comp_ids[i + 1]
            box_a = boxes.get(cid_a)
            box_b = boxes.get(cid_b)
            if box_a is None or box_b is None:
                continue
            ax.annotate("",
                        xy=(box_b.x_left, box_b.y_center),
                        xytext=(box_a.x_right, box_a.y_center),
                        arrowprops=dict(arrowstyle="->", color=BRANCH_LINE_COLOR,
                                        lw=1.5, shrinkA=0, shrinkB=0),
                        zorder=2)

        # --- Vertical return from last branch component to main ---
        if branch.tap_to and branch.tap_to.comp_id in boxes:
            main_box = boxes[branch.tap_to.comp_id]
            main_comp = components.get(branch.tap_to.comp_id)

            if main_comp and main_comp.comp_type == "pipe" and main_comp.volume_count > 0:
                vol_frac = (branch.tap_to.volume_idx - 0.5) / main_comp.volume_count
                ret_x = main_box.x_left + vol_frac * main_box.width
            else:
                ret_x = main_box.x_center

            ret_y = main_box.y_bottom  # bottom of main component

            last_cid = branch.comp_ids[-1]
            last_box = boxes.get(last_cid)
            if last_box:
                _draw_tap_marker(ax, ret_x, ret_y, "up")

                mid_y = ret_y - DROP_MIN
                src_y = last_box.y_top

                if abs(ret_x - last_box.x_center) < 0.1:
                    ax.annotate("",
                                xy=(ret_x, ret_y),
                                xytext=(last_box.x_center, src_y),
                                arrowprops=dict(arrowstyle="->",
                                                color=RETURN_LINE_COLOR, lw=1.5,
                                                linestyle="dashed",
                                                shrinkA=0, shrinkB=0),
                                zorder=2)
                else:
                    route_x = [last_box.x_center, last_box.x_center, ret_x, ret_x]
                    route_y = [src_y, mid_y, mid_y, ret_y]
                    ax.plot(route_x, route_y, color=RETURN_LINE_COLOR,
                            lw=1.5, linestyle="dashed", zorder=2)
                    ax.annotate("",
                                xy=(route_x[-1], route_y[-1]),
                                xytext=(route_x[-2], route_y[-2]),
                                arrowprops=dict(arrowstyle="->",
                                                color=RETURN_LINE_COLOR, lw=1.5,
                                                linestyle="dashed",
                                                shrinkA=0, shrinkB=0),
                                zorder=2)


# =========================================================================
# Phase 4: Main entry point
# =========================================================================

def generate_nodalization_diagram(
    components: Dict[int, R5Component],
    output_path: str,
    title: str = "RELAP5 Nodalization Diagram",
) -> None:
    """Generate an engineering nodalization schematic from RELAP5 components.

    Args:
        components: Dict of card_id → R5Component from parse_relap5_deck().
        output_path: Path for the output image (.png or .svg).
        title: Diagram title.
    """
    if not components:
        return

    # --- Step 1: Topology analysis ---
    plan = analyze_topology(components)

    # --- Step 2: Layout assignment ---
    boxes = assign_positions(plan, components)

    # --- Step 3: Compute figure size ---
    all_x_right = max(
        (b.x_right for b in boxes.values()), default=20.0
    )
    num_rows = 1 + len(plan.branches)
    fig_w = max(18, all_x_right + 3.0)
    fig_h = max(8, num_rows * ROW_SPACING + 4.0)

    fig, ax = plt.subplots(1, 1, figsize=(fig_w, fig_h))
    ax.set_facecolor(BG_COLOR)
    fig.patch.set_facecolor(BG_COLOR)

    # --- Step 4: Draw components ---
    for cid, box in boxes.items():
        comp = components.get(cid)
        if comp is None:
            continue

        if comp.comp_type == "tmdpvol":
            _draw_tmdpvol(ax, comp, box)
        elif comp.comp_type == "pipe":
            _draw_pipe(ax, comp, box)
        elif comp.comp_type == "valve":
            _draw_valve(ax, comp, box)
        elif comp.comp_type == "sngljun":
            _draw_sngljun(ax, comp, box)

    # --- Step 5: Draw connections ---
    _draw_main_connections(ax, plan, boxes)
    _draw_branch_connections(ax, plan, boxes, components)

    # --- Step 6: Title and layout ---
    # Compute y range: main row + title above, branch rows below
    branch_bottom = MAIN_ROW_Y - len(plan.branches) * ROW_SPACING - 3.0
    if not plan.branches:
        branch_bottom = MAIN_ROW_Y - 3.0
    title_top = MAIN_ROW_Y + TMDPVOL_H + 4.0

    ax.set_xlim(0, fig_w)
    ax.set_ylim(branch_bottom, title_top)
    ax.axis("off")
    ax.set_title(title, fontsize=30, fontweight="bold", pad=12,
                 fontfamily=FONT_FAMILY)

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor=BG_COLOR, edgecolor="none")
    plt.close(fig)
