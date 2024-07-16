from uuid import uuid1
from dataclasses import dataclass
from utils.collections import first_or_default


@dataclass
class Passenger:
    id: str
    name: str
    seat: int


passengers: dict[str, Passenger] = {
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
    )
}


def by_id(passenger_id: str) -> Passenger | None:
    return passengers.get(passenger_id, None)


def by_seat(seat: int) -> Passenger | None:
    return first_or_default(passengers.values(), lambda p: p.seat == seat)
