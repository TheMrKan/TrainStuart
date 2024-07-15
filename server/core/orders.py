from datetime import datetime
from dataclasses import dataclass
import uuid

from server.core.products import Product
import server.core.products as products
from server.core.baskets import Position
import server.core.baskets as baskets
from copy import deepcopy



@dataclass
class Order:
    id: str
    passenger_id: str
    positions: list[Position]
    created: datetime
    payed: datetime | None
    total_price: float


orders = {}


def create(passenger_id: str, positions: list[Position]) -> Order:
    order = Order(
        str(uuid.uuid1()), 
        passenger_id, 
        deepcopy(positions), 
        datetime.now(), 
        None, 
        baskets.get_total_price(positions)
        )

    orders[order.id] = order

    return order


def get(order_id: str) -> Order | None:
    return orders.get(order_id, None)
    