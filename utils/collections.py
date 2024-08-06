from typing import Iterable, Callable, Any


def first_or_default(iterable: Iterable, predicate: Callable[[Any], bool], default: Any = None):
    for elem in iterable:
        if predicate(elem):
            return elem
    return default


def first(iterable: Iterable):
    for elem in iterable:
        return elem
