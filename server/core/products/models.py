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