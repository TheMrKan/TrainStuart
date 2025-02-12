from fastapi import APIRouter, status as http_status
from typing import List
from utils.collections import first_or_default

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


@router.post("/{request_id}/status")
def set_delivery_status(request_id: str, status: int):
    deliv: delivery.RequestedDelivery = delivery.deliveries.get(request_id)
    if not deliv:
        raise http_status.HTTP_404_NOT_FOUND

    delivery.update_status(deliv, delivery.DeliveryStatus(status))
    return {}
