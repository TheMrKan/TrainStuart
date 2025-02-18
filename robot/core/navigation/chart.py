import json
from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional
from robot.config import instance as config


Vector2 = Tuple[int, int]

WALL_Y = 100
LINE_Y = 0
VENDING_LINE_Y = 70


@dataclass
class Point:
    id: str
    x: int
    y: int


@dataclass
class Zone:
    id: str
    p0: Vector2
    p1: Vector2


points: Dict[str, Point] = {}
zones: Dict[str, Zone] = {}


def parse_vector_2(data: dict) -> Vector2:
    return int(data["x"]), int(data["y"])


def load():
    with open(config.data_dir + "/chart.json", "r") as f:
        raw: Dict = json.load(f)
        raw_points = raw.get("points", [])
        for r in raw_points:
            p = Point(str(r["id"]), *parse_vector_2(r))
            points[p.id] = p

        raw_zones = raw.get("zones", [])
        for r in raw_zones:
            zone = Zone(str(r["id"]), parse_vector_2(r["p0"]), parse_vector_2(r["p1"]))
            zones[zone.id] = zone


def get_absolute_position(point_id: str, rel_pos: Vector2) -> Vector2:
    point = points[point_id]
    return point.x + rel_pos[0], point.y + rel_pos[1]


def get_point_position(point_id: str) -> Vector2:
    point = points[point_id]
    return point.x, point.y


def get_points() -> List[Point]:
    return list(points.values())


def get_position_for_seat(seat: int) -> Vector2:
    seat_pos = get_point_position(f"seat_{seat}")
    return seat_pos[0] - 20, 0


def is_inside_zone(pos: Vector2, zone: Zone) -> bool:
    return zone.p0[0] <= pos[0] <= zone.p1[0] and zone.p0[1] >= pos[1] >= zone.p1[1]


def get_zone(point: Vector2) -> Optional[Zone]:
    for zone in zones.values():
        if is_inside_zone(point, zone):
            return zone
    return None



