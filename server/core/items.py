from dataclasses import dataclass
from typing import Optional


@dataclass
class Item:
    id: str


items: dict = {
    "water_still_05": Item("water_still_05"),
    "cola": Item("cola"),
    "glass": Item("glass")
}


def by_id(item_id: str) -> Optional[Item]:
    return items.get(item_id, None)
