from dataclasses import dataclass


@dataclass
class Item:
    id: str


items: dict[str, Item] = {
    "water_still_0,5": Item("water_still_0,5"),
    "cola": Item("cola")
}


def by_id(item_id: str) -> Item | None:
    return items.get(item_id, None)
