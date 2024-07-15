from server.core.baskets.models import PassengerBasket
from server.core.products.models import Product, OutOfStockError
import server.core.baskets.repository as baskets_repo
import server.core.products.repository as products_repo
import server.core.products.manager as products_manager


def get_total_price(position_prices: list[float]) -> float:
    return sum(position_prices)


def create_basket(passenger_id: str) -> PassengerBasket:
        basket = PassengerBasket(passenger_id, {})
        baskets_repo.add(basket)
        return basket


def update_basket(passenger_id: str, product: Product, amount: int):
    if amount <= 0:
        remove_from_basket(passenger_id, product)
        return
    
    basket = baskets_repo.by_id(passenger_id) or create_basket(passenger_id)
    validate_product(product, amount)
    basket.positions[product.id] = amount


def validate_product(product: Product, amount: int):
    if not products_manager.is_available(product, amount):
         raise OutOfStockError(product, amount, product.amount_left)


def remove_from_basket(passenger_id: str, product: Product):
    basket = baskets_repo.by_id(passenger_id)
    if basket and product.id in basket.positions.keys():
         del basket.positions[product.id]


def clear_basket(passenger_id: str):
     basket = baskets_repo.by_id(passenger_id)
     if basket:
        basket.positions.clear()
        baskets_repo.remove(passenger_id)
