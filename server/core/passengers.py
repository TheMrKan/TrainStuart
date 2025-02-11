from uuid import uuid1
from dataclasses import dataclass
from utils.collections import first_or_default
from utils.faces import FaceDescriptor
from typing import Optional, Generator
import numpy


@dataclass
class Passenger:
    id: str
    name: str
    seat: int
    ticket: str
    passport: Optional[str]
    face_descriptor: Optional[FaceDescriptor]


passengers: dict = {
    (uuid := str(uuid1())):
    Passenger(
        uuid,
        "Ivan Ivanov",
        1,
        "1",
        "3620896892",
        numpy.zeros((128, ))
    ),
    (uuid := str(uuid1())):
    Passenger(
        uuid,
        "Petya Petrov",
        2,
        "2",
        "3610382561",
        numpy.zeros((128,))
    ),
    "robot":
    Passenger(
        "robot",
        "Robot",
        3,
        "3",
        None,
        None
    )
}


def with_passport() -> Generator[Passenger, None, None]:
    return (p for p in passengers.values() if p.passport)


def by_id(passenger_id: str) -> Optional[Passenger]:
    return passengers.get(passenger_id, None)


def by_seat(seat: int) -> Optional[Passenger]:
    return first_or_default(passengers.values(), lambda p: p.seat == seat)


def by_ticket(ticket: str) -> Optional[Passenger]:
    return first_or_default(passengers.values(), lambda p: p.ticket == ticket)


def by_passport(passport: str) -> Optional[Passenger]:
    return first_or_default(passengers.values(), lambda p: p.passport == passport)
