from uuid import uuid1
from dataclasses import dataclass
from utils.collections import first_or_default
from utils.faces import FaceDescriptor
from typing import Optional, Generator, Dict
import numpy
import json


@dataclass
class Passenger:
    id: str
    name: str
    seat: int
    ticket: str
    passport: Optional[str]
    face_descriptor: Optional[FaceDescriptor]


passengers: Dict[str, Passenger]


def load():
    global passengers
    passengers = {}

    with open("data/passengers.json", encoding="utf-8") as f:
        data = json.load(f)
        for raw in data:
            passenger = Passenger(**raw)
            if passenger.face_descriptor is not None:
                passenger.face_descriptor = numpy.asarray(passenger.face_descriptor)
            passengers[passenger.id] = passenger

    print(f"Loaded {len(passengers)} passengers")


def save():
    data = []
    for passenger in passengers.values():
        raw = {
            "id": passenger.id,
            "name": passenger.name,
            "seat": passenger.seat,
            "ticket": passenger.ticket,
            "passport": passenger.passport,
            "face_descriptor": list(map(float, passenger.face_descriptor)) if passenger.face_descriptor is not None else None
        }
        data.append(raw)

    with open("data/passengers.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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


def update_face_descriptor(passenger_id: str, descriptor: Optional[FaceDescriptor]):
    passengers[passenger_id].face_descriptor = descriptor
    save()
    print(f"Updated face descriptor for passenger {passenger_id}")
