from fastapi import APIRouter
from server.core import calls, delivery

router = APIRouter(prefix="/robot")


__sent_calls = set()
__has_new_delivery = False


@router.get("/polling/")
def polling():
    updates = {}

    for call in calls.active_calls:
        if call in __sent_calls:
            continue

        updates.setdefault("calls", {"new_calls": []})
        updates["calls"]["new_calls"].append(call)
        __sent_calls.add(call)

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
