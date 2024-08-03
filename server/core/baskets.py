from dataclasses import dataclass
from server.core.products import Product
import server.core.products as products
from typing import Iterable, Optional
from utils.collections import first_or_default


@dataclass
class Position:
    product: Product
    amount: int
    total_price: float


@dataclass
class Basket:
    passenger_id: str
    positions: list
    total_price: float


baskets: dict = {}


def get_basket(passenger_id: str) -> Optional[Basket]:
    return baskets.get(passenger_id, None)


def create_basket(passenger_id: str) -> Basket:
    basket = Basket(passenger_id, [], 0)
    baskets[passenger_id] = basket
    return basket


def get_total_price(positions: Iterable[Position]) -> float:
    return sum(pos.total_price for pos in positions)


def update_basket(passenger_id: str, product: Product, amount: int):
    if amount <= 0:
        remove_from_basket(passenger_id, product)
        return
    
    products.assert_available_amount(product, amount)
    
    basket = get_basket(passenger_id) or create_basket(passenger_id)
    position: Optional[Position] = first_or_default(basket.positions, lambda p: p.product.id == product.id)
    if not position:
        position = Position(product, 0, 0)
        basket.positions.append(position)

    position.amount = amount
    position.total_price = products.get_price(product, position.amount)

    basket.total_price = get_total_price(basket.positions)


def remove_from_basket(passenger_id: str, product: Product):
    basket = get_basket(passenger_id)
    if basket:
        position = first_or_default(basket.positions, lambda p: p.product.id == product.id)
        if position:
            basket.positions.remove(position)
    basket.total_price = get_total_price(basket.positions)


def clear_basket(passenger_id: str):
    basket = get_basket(passenger_id)
    if basket:
        basket.positions.clear()
        basket.total_price = 0
