from datetime import datetime
from dataclasses import dataclass
import uuid
from copy import deepcopy
from server.core.misc import CoreError
from typing import Optional

from server.core.products import Product
import server.core.products as products
from server.core.baskets import Position
import server.core.baskets as baskets
import server.core.delivery as delivery
import server.core.passengers as passengers
from server.core.passengers import Passenger


@dataclass
class Order:
    id: str
    passenger: Passenger
    positions: list
    created: datetime
    payed: Optional[datetime]
    total_price: float


class OrderCompletionError(CoreError):
    order: Order
    reason: Optional[CoreError]

    def __init__(self, order: Order, reason: Optional[CoreError], *args: object) -> None:
        self.order = order
        self.reason = reason
        super().__init__(*args)


orders = {}


def by_id(order_id: str) -> Optional[Order]:
    return orders.get(order_id, None)


def create(passenger: Passenger, positions: list) -> Order:
    order = Order(
        str(uuid.uuid1()), 
        passenger, 
        deepcopy(positions), 
        datetime.now(), 
        None, 
        baskets.get_total_price(positions)
        )

    orders[order.id] = order

    return order


def mark_payed(order: Order):
    order.payed = datetime.now()

    baskets.clear_basket(order.passenger.id)

    try:
        delivery.request_positions(order.positions, order.passenger.seat)
    except delivery.UndeliverablePositionError as e:
        raise OrderCompletionError(order, e)
