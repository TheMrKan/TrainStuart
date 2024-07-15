from fastapi import APIRouter
from server.routers.models import DeliveryRequest


router = APIRouter(prefix="/delivery")


@router.get("/list/")
def list_deliveries() -> list[DeliveryRequest]:
    pass


@router.post("/take/")
def take_delivery(deliveries: list[str]):
    pass


@router.post("/{request_id}/status")
def set_delivery_status(request_id: str, status: int):
    pass