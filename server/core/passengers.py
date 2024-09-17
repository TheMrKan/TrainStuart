from uuid import uuid1
from dataclasses import dataclass
from utils.collections import first_or_default
from typing import Optional


@dataclass
class Passenger:
    id: str
    name: str
    seat: int


passengers: dict = {
    (uuid := str(uuid1())):
    Passenger(
        uuid,
        "Ivan Ivanov",
        1
    ),
    (uuid := str(uuid1())):
    Passenger(
        uuid,
        "Petya Petrov",
        2
    ),
    "robot":
    Passenger(
        "robot",
        "Robot",
        3,
    )
}


def by_id(passenger_id: str) -> Optional[Passenger]:
    return passengers.get(passenger_id, None)


def by_seat(seat: int) -> Optional[Passenger]:
    return first_or_default(passengers.values(), lambda p: p.seat == seat)
