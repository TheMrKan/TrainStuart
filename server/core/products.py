from dataclasses import dataclass
from server.core.misc import CoreError


@dataclass
class Product:
    id: str
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
    "water_still_0,5": Product(
        "water_still_0,5",
        "Минеральная вода 0,5 л",
        "Пол литра минеральной воды без газа в пластиковой бутылке",
        "http://127.0.0.1:8000/static/water_still_0,5_icon.png",
        "http://127.0.0.1:8000/static/water_still_0,5_image.png",
        50,
        5
    ),
    "cola": Product(
        "cola",
        "CocaCola 0,33 л",
        "0,33 литра CocaCola в оригинальной жестяной банке",
        "http://127.0.0.1:8000/static/cola_icon.png",
        "http://127.0.0.1:8000/static/cola_image.png",
        100,
        1
    ),
}


def all() -> list[Product]:
    return list(FAKE_PRODUCTS_DB.values())


def by_id(product_id: str) -> Product | None:
    return FAKE_PRODUCTS_DB.get(product_id, None)


def is_available(product: Product, amount: int = 1) -> bool:
    return product.amount_left >= amount


def get_price(product: Product, amount: int) -> float:
    return product.price * amount


def assert_available_amount(product: Product, amount: int):
    if not is_available(product, amount):
         raise OutOfStockError(product, amount, product.amount_left)