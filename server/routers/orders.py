from fastapi import APIRouter
from server.routers.models import OrderDetails


router = APIRouter(prefix="/orders")


@router.get("/{order_id}/")
def get_order(order_id: str) -> OrderDetails:
    pass


@router.post("/{order_id}/pay/")
def pay_order(order_id: str):
    pass