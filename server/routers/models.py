from pydantic import BaseModel
import datetime
from dataclasses import dataclass


@dataclass
class ProductSummary():
    id: str
    name: str
    icon_url: str
    price: float
    is_available: bool


@dataclass
class ProductDetails():
    id: str
    name: str
    image_url: str
    description: str
    price: float
    is_available: bool


@dataclass
class BasketPosition():
    product_id: str
    amount: int
    total_price: float


@dataclass
class PassengerBasket():
    positions: list[BasketPosition]
    total_price: float


class BasketPositionUpdate(BaseModel):
    product_id: str
    amount: int


class BasketPositionRemove(BaseModel):
    product_id: str


@dataclass
class OrderPosition():
    product_id: str
    amount: int
    total_price: float


@dataclass
class OrderDetails():
    id: str
    passenger_id: str
    positions: list[OrderPosition]
    created: datetime.datetime
    payed: datetime.datetime | None
    total_price: float


@dataclass
class RequestedDelivery():
    id: str
    item_id: str
    seat: int
    priority: int