from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from server.routers.models import PassengerBasket, BasketPosition, BasketPositionUpdate, BasketPositionRemove, OrderDetails, OrderPosition
import server.core.products as products
from server.core.products import OutOfStockError
import server.core.baskets as baskets
import server.core.orders as orders


router = APIRouter(prefix="/baskets")


@router.get("/{passenger_id}/")
def get_basket(passenger_id: str) -> PassengerBasket:
    products = baskets.get_basket(passenger_id)

    basket = PassengerBasket([], 0)
    for pos in products.positions:
        position = BasketPosition(pos.product.id, pos.amount, pos.total_price)
        basket.positions.append(position)

    basket.total_price = products.total_price
    return basket


@router.post("/{passenger_id}/update/")
def update_basket(passenger_id: str, req: BasketPositionUpdate):
    product = products.by_id(req.product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    
    try:
        baskets.update_basket(passenger_id, product, req.amount)
    except OutOfStockError:
        raise HTTPException(409, "Out of stock")


@router.post("/{passenger_id}/remove/")
def remove_from_basket(passenger_id: str, req: BasketPositionRemove):
    product = products.by_id(req.product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    baskets.remove_from_basket(passenger_id, product)


@router.post("/{passenger_id}/checkout/")
def checkout_basket(passenger_id: str) -> OrderDetails:
    basket = baskets.get_basket(passenger_id)
    if not any(basket.positions):
        raise HTTPException(409, "The basket is empty")

    try:
        order = orders.create(passenger_id, basket.positions)
    except OutOfStockError as e:
        raise HTTPException(409, f"Out of stock. Product: {e.product.id}. Requested: {e.requested_amount}. Available: {e.available_amount}")
    
    details_positions = [OrderPosition(p.product.id, p.amount, p.total_price) for p in order.positions]
    details = OrderDetails(order.id, order.passenger_id, details_positions, order.created, order.payed, order.total_price)

    return details