from server.core.products.models import Product


def is_available(product: Product, amount: int = 1) -> bool:
    return product.amount_left >= amount


def get_price(product: Product, amount: int) -> float:
    return product.price * amount
