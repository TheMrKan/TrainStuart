import json

from fastapi import APIRouter, File, UploadFile, status, Request
from server.core import calls, delivery, documents, passengers
from server.routers.models import Passenger
from typing import List, Optional
import numpy

router = APIRouter(prefix="/robot")


__has_new_delivery = False


@router.get("/polling/")
def polling():
    updates = {}

    for call in calls.active_calls:

        updates.setdefault("calls", {"new_calls": []})
        updates["calls"]["new_calls"].append(call)

    calls.active_calls.clear()

    global __has_new_delivery
    if __has_new_delivery:
        updates.setdefault("deliveries", {})
        updates["deliveries"]["has_new"] = True
        __has_new_delivery = False

    return updates


def on_new_delivery(*args):
    global __has_new_delivery
    __has_new_delivery = True


# подписка на событие
delivery.on_new_delivery.append(on_new_delivery)


@router.post("/document/")
def document(file: UploadFile):
    loaded = documents.load_file(file.file)
    passport = documents.process_ocr(loaded)
    if not passport:
        return {"success": False, "error": "OCR failed"}
    print(f"Got passport number: {passport}")

    passenger = passengers.by_passport(passport)
    if not passenger:
        return {"success": False, "error": "Passenger not found"}
    print(f"Got passenger: {passenger.name}")

    return {"success": True, "passenger_id": passenger.id}


@router.get("/passengers/")
def get_passengers():
    return [Passenger(p.id, p.seat, p.ticket, p.name, p.passport,
                      list(map(float, p.face_descriptor)) if p.face_descriptor is not None else None)
            for p in passengers.passengers.values()]


@router.post("/passengers/{passenger_id}/face_descriptor")
async def update_face_descriptor(request: Request, passenger_id: str):
    descriptor = json.loads(await request.json())
    if len(descriptor) != 128:
        raise AssertionError("Descriptor length must be 128")

    converted_descriptor = numpy.asarray(descriptor, dtype=numpy.float32)

    try:
        passengers.update_face_descriptor(passenger_id, converted_descriptor)
    except KeyError:
        return status.HTTP_404_NOT_FOUND

    return status.HTTP_200_OK
