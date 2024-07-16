from dataclasses import dataclass
from datetime import datetime
from uuid import uuid1
from typing import Iterable, Iterator
from enum import Enum
import math
from server.core.misc import CoreError

import server.core.items as items
from server.core.items import Item
from server.core.baskets import Position


class DeliveryStatus(Enum):
    REQUESTED = 0
    PROCESSING = 1
    COMPLETED = 2
    FAILED = 3


@dataclass
class RequestedDelivery:
    id: str
    item: Item
    status: DeliveryStatus
    seat: int
    initial_priority: int
    requested: datetime


class UndeliverablePositionError(CoreError):
    position: Position

    def __init__(self, position: Position) -> None:
        self.position = position
        self.message = f"Cannot deliver position {position.product.id} ({position.amount})"
        super().__init__(self.message)
        

deliveries: dict[str, RequestedDelivery] = {}


def requested() -> Iterator[RequestedDelivery]:
    return (d for d in deliveries.values() if d.status == DeliveryStatus.REQUESTED)


def by_id(delivery_id: str) -> RequestedDelivery | None:
    return deliveries.get(delivery_id, None)


def request_positions(positions: Iterable[Position], seat: int, initial_priority: int = 1) -> list[RequestedDelivery]:
    result = []
    for pos in positions:
        item = items.by_id(pos.product.item_id)
        if not item:
            raise UndeliverablePositionError(pos)
        result.extend(request_many(item, pos.amount, seat, initial_priority))
    return result


def request_many(item: Item, amount: int, seat: int, initial_priority: int = 1) -> list[RequestedDelivery]:
    return [request(item, seat, initial_priority) for _ in range(amount)]


def request(item: Item, seat: int, initial_priority: int) -> RequestedDelivery:
    delivery = RequestedDelivery(
        str(uuid1()),
        item,
        DeliveryStatus.REQUESTED,
        seat,
        initial_priority,
        datetime.now()
    )

    deliveries[delivery.id] = delivery
    return delivery


def get_priority(delivery: RequestedDelivery) -> int:
    priority = delivery.initial_priority
    time_priority = int(round((datetime.now() - delivery.requested).total_seconds() / 60))
    priority += time_priority
    return priority