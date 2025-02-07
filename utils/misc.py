from typing import Tuple


def are_nearly_equal(a: float, b: float, limit: float = 3):
    return abs(a - b) <= limit


def sqr_distance(a: Tuple[int, int], b: Tuple[int, int]):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2