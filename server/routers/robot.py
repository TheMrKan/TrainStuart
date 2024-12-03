from fastapi import APIRouter
from server.core import calls

router = APIRouter(prefix="/robot")


__sent_calls = set()


@router.get("/polling/")
def polling():
    updates = {}

    for call in calls.active_calls:
        if call in __sent_calls:
            continue

        updates.setdefault("calls", {"new_calls": []})
        updates["calls"]["new_calls"].append(call)
        __sent_calls.add(call)

    return updates

