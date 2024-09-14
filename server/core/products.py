from dataclasses import dataclass
from typing import Optional
from server.core.misc import CoreError


@dataclass
class Product:
    id: str
    item_id: str
    name: str
    description: str
    icon_url: str
    image_url: str
    price: float
    amount_left: int


class OutOfStockError(CoreError):
    product: Product
    requested_amount: int
    available_amount: int
    
    def __init__(self, product: Product, requested_amount: int, available_amount: int, *args: object) -> None:
        self.product = product
        self.requested_amount = requested_amount
        self.available_amount = available_amount
        super().__init__(*args)


FAKE_PRODUCTS_DB = {
    "water_still_05": Product(
        "water_still_05",
        "water_still_05",
        "Минеральная вода 0,5 л",
        "Пол литра минеральной воды без газа в пластиковой бутылке",
        "/images/shop/water.png",
        "/images/shop/water.png",
        50,
        5
    ),
    "cola": Product(
        "cola",
        "cola",
        "CocaCola 0,33 л",
        "0,33 литра CocaCola в оригинальной жестяной банке",
        "/images/shop/blackTea.png",
        "/images/shop/blackTea.png",
        100,
        1
    ),
}


def all() -> list:
    return list(FAKE_PRODUCTS_DB.values())


def by_id(product_id: str) -> Optional[Product]:
    return FAKE_PRODUCTS_DB.get(product_id, None)


def is_available(product: Product, amount: int = 1) -> bool:
    return product.amount_left >= amount


def get_price(product: Product, amount: int) -> float:
    return product.price * amount


def assert_available_amount(product: Product, amount: int):
    if not is_available(product, amount):
         raise OutOfStockError(product, amount, product.amount_left)