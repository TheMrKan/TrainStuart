from dataclasses import dataclass
from typing import Optional


@dataclass
class Item:
    id: str


items: dict = {
    "water_still_0,5": Item("water_still_0,5"),
    "cola": Item("cola")
}


def by_id(item_id: str) -> Optional[Item]:
    return items.get(item_id, None)
