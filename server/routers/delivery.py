from fastapi import APIRouter
from typing import List

from server.routers.models import RequestedDelivery
import server.core.delivery as delivery


router = APIRouter(prefix="/delivery")


@router.get("/list/")
def list_deliveries() -> List[RequestedDelivery]:
    requested = delivery.requested()
    result = [RequestedDelivery(
        d.id,
        d.item.id,
        d.seat,
        delivery.get_priority(d)
    ) for d in requested]
    return result


@router.post("/take/")
def take_delivery(deliveries: List[str]):
    pass


@router.post("/{request_id}/status")
def set_delivery_status(request_id: str, status: int):
    pass