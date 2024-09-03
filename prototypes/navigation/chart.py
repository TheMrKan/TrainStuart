import json
from dataclasses import dataclass
from typing import Dict, Tuple, List


@dataclass
class Point:
    id: str
    x: int
    y: int


points: Dict[str, Point] = {}


def load_map():
    with open("chart.json", "r") as f:
        raw = json.load(f)
        for r in raw:
            p = Point(str(r["id"]), int(r["x"]), int(r["y"]))
            points[p.id] = p


def get_absolute_position(point_id: str, rel_x: int, rel_y: int) -> Tuple[int, int]:
    point = points[point_id]
    return point.x + rel_x, point.y + rel_y


def get_point_position(point_id: str) -> Tuple[int, int]:
    point = points[point_id]
    return point.x, point.y


def get_points() -> List[Point]:
    return list(points.values())


def test():
    load_map()
    print(get_absolute_position("R0", 50, 100))


if __name__ == "__main__":
    test()

