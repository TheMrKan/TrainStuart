from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from server.routers.models import PassengerBasket, BasketPosition, BasketPositionUpdate, BasketUpdated, \
    BasketPositionRemove, OrderDetails, OrderPosition
from server.routers.auth import get_passenger
import server.core.products as products
from server.core.products import OutOfStockError
import server.core.baskets as baskets
import server.core.orders as orders
import server.core.passengers as passengers


router = APIRouter(prefix="/baskets")


@router.get("/")
def get_basket(passenger_id=Depends(get_passenger)) -> PassengerBasket:
    basket = PassengerBasket([], 0)

    products = baskets.get_basket(passenger_id)
    if not products:
        return basket
    
    for pos in products.positions:
        position = BasketPosition(pos.product.id, pos.amount, pos.total_price)
        basket.positions.append(position)

    basket.total_price = products.total_price
    return basket


@router.post("/update/")
def update_basket(req: BasketPositionUpdate, passenger_id=Depends(get_passenger)) -> BasketUpdated:
    product = products.by_id(req.product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    
    try:
        basket = baskets.update_basket(passenger_id, product, req.amount)
        pos_price = [p for p in basket.positions if p.product is product][0].total_price if req.amount > 0 else 0
        return BasketUpdated(pos_price, basket.total_price)
    except OutOfStockError:
        raise HTTPException(409, "Out of stock")


@router.post("/remove/")
def remove_from_basket(req: BasketPositionRemove, passenger_id=Depends(get_passenger)):
    product = products.by_id(req.product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    baskets.remove_from_basket(passenger_id, product)


@router.post("/checkout/")
def checkout_basket(passenger_id=Depends(get_passenger)) -> OrderDetails:
    passenger = passengers.by_id(passenger_id)
    if not passenger:
        raise HTTPException(401, "Passenger not found")

    basket = baskets.get_basket(passenger_id)
    if not basket or not any(basket.positions):
        raise HTTPException(409, "The basket is empty")

    try:
        order = orders.create(passenger, basket.positions)
    except OutOfStockError as e:
        raise HTTPException(409, f"Out of stock. Product: {e.product.id}. Requested: {e.requested_amount}. Available: {e.available_amount}")
    
    details_positions = [OrderPosition(p.product.id, p.amount, p.total_price) for p in order.positions]
    details = OrderDetails(order.id, order.passenger.id, details_positions, order.created, order.payed, order.total_price)

    return details