from typing import Dict, Optional

from utils.faces import FaceDescriptor, get_nearest_descriptor_index
from utils.collections import first_or_default
from robot.core import server


class Person:
    id: str
    name: Optional[str]
    seat: int
    passport: Optional[str]
    face_descriptor: Optional[FaceDescriptor]

    def __init__(self,
                 id: str,
                 seat: int,
                 name: Optional[str] = None,
                 passport: Optional[str] = None,
                 face_descriptor: Optional[FaceDescriptor] = None):
        self.id = id
        self.seat = seat
        self.name = name
        self.passport = passport
        self.face_descriptor = face_descriptor

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.name or 'NONAME'}(seat: {self.seat})"


__persons: Dict[str, Person] = {

}
__available_id = len(__persons)


def load():
    server_data = server.get_passengers()
    for passenger in server_data:
        __persons[passenger["id"]] = Person(passenger["id"], passenger["seat"], passenger["name"],
                                            passenger["passport"], passenger["face_descriptor"])


def with_faces():
    for person in __persons.values():
        if person.face_descriptor is not None:
            yield person


def get_by_id(id: str) -> Optional[Person]:
    return __persons.get(id)


def get_by_passport(passport_number: str) -> Optional[Person]:
    return first_or_default(__persons.values(), lambda p: p.passport == passport_number)


def find_by_face_descriptor(descriptor: FaceDescriptor, threshold: float = 0.5) -> Optional[Person]:
    persons_with_faces = tuple(with_faces())
    descriptors = [p.face_descriptor for p in persons_with_faces]
    index = get_nearest_descriptor_index(descriptor, descriptors, threshold)
    if index == -1:
        return None
    return persons_with_faces[index]


def add_by_face(descriptor: FaceDescriptor) -> Person:
    global __available_id
    person = Person()
    person.id = __available_id
    person.face_descriptor = descriptor
    __persons[person.id] = person
    __available_id = __find_new_available_id()
    return person


def __find_new_available_id() -> int:
    return __available_id + 1


def update_face_descriptor(passenger_id: str, descriptor: Optional[FaceDescriptor]):
    __persons[passenger_id].face_descriptor = descriptor
    server.update_passenger_face_descriptor(passenger_id, descriptor)