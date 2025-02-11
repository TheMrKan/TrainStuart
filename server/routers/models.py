from pydantic import BaseModel
import datetime
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class ProductSummary:
    id: str
    name: str
    icon_url: str
    price: float
    is_available: bool


@dataclass
class ProductDetails:
    id: str
    name: str
    icon_url: str
    image_url: str
    description: str
    price: float
    is_available: bool


@dataclass
class BasketPosition:
    product_id: str
    amount: int
    total_price: float


@dataclass
class PassengerBasket:
    positions: List[BasketPosition]
    total_price: float


class BasketPositionUpdate(BaseModel):
    product_id: str
    amount: int


@dataclass
class BasketUpdated:
    position_price: float
    total_price: float


class BasketPositionRemove(BaseModel):
    product_id: str


@dataclass
class OrderPosition:
    product_id: str
    amount: int
    total_price: float


@dataclass
class OrderDetails:
    id: str
    passenger_id: str
    positions: list
    created: datetime.datetime
    payed: Optional[datetime.datetime]
    total_price: float


@dataclass
class RequestedDelivery:
    id: str
    item_id: str
    seat: int
    priority: int


@dataclass
class Passenger:
    id: str
    seat: int
    name: Optional[str]
    passport: Optional[str]
    face_descriptor: List[int]
