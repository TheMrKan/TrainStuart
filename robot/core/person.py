from typing import Dict, Optional

from utils.faces import FaceDescriptor, get_nearest_descriptor_index


class Person:
    id: int
    name: Optional[str]
    face_descriptor: Optional[FaceDescriptor]

    def __init__(self, id: int = 0):
        self.id = id
        self.name = None
        self.face_descriptor = None

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.name or 'NONAME'}({self.id})"


__persons: Dict[int, Person] = {

}
__available_id = len(__persons)


def with_faces():
    for person in __persons.values():
        if person.face_descriptor is not None:
            yield person


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