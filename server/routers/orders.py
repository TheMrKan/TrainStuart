from fastapi import APIRouter, HTTPException
from datetime import datetime

from server.routers.models import OrderDetails, OrderPosition
import server.core.orders as orders


router = APIRouter(prefix="/orders")


@router.get("/{order_id}/")
def get_order(order_id: str) -> OrderDetails:
    order = orders.by_id(order_id)
    if not order:
        raise HTTPException(404, "Order not found")

    details_positions = [OrderPosition(p.product.id, p.amount, p.total_price) for p in order.positions]
    details = OrderDetails(order.id, order.passenger.id, details_positions, order.created, order.payed, order.total_price)

    return details


@router.post("/{order_id}/pay/")
def pay_order(order_id: str):
    order = orders.by_id(order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    
    try:
        orders.mark_payed(order)
    except orders.OrderCompletionError as e:
        raise HTTPException(500, f"Failed to complete the order. Reason: {e.reason}")
