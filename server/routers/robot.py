from fastapi import APIRouter, File, UploadFile
from server.core import calls, delivery, documents, passengers
from server.routers.models import Passenger

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

    passenger = documents.try_find_passenger(passport)
    if not passenger:
        return {"success": False, "error": "Passenger not found"}

    return {"success": True, "passenger_id": passenger.id}


@router.get("/passengers/")
def get_passengers():
    return [Passenger(p.id, p.seat, p.name, p.passport, list(p.face_descriptor) if p.face_descriptor is not None else [])
            for p in passengers.passengers.values()]
