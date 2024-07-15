from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from server.routers.models import PassengerBasket, BasketPosition, BasketPositionUpdate, BasketPositionRemove, OrderDetails
from server.core.products.models import OutOfStockError
import server.core.baskets.repository as baskets_repo
import server.core.baskets.manager as baskets_manager
import server.core.products.repository as products_repo
import server.core.products.manager as products_manager


router = APIRouter(prefix="/baskets")


@router.get("/{passenger_id}/")
def get_basket(passenger_id: str) -> PassengerBasket:
    products = baskets_repo.by_id(passenger_id)

    basket = PassengerBasket([], 0)
    for prod_id, amount in products.positions.items():
        product = products_repo.by_id(prod_id)
        if not product or not products_manager.is_available(product):
            continue

        price = products_manager.get_price(product, amount)
        position = BasketPosition(prod_id, amount, price)
        basket.positions.append(position)

    basket.total_price = baskets_manager.get_total_price([pos.total_price for pos in basket.positions])
    return basket


@router.post("/{passenger_id}/update/")
def update_basket(passenger_id: str, req: BasketPositionUpdate):
    product = products_repo.by_id(req.product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    
    try:
        baskets_manager.update_basket(passenger_id, product, req.amount)
    except OutOfStockError:
        raise HTTPException(409, "Out of stock")


@router.post("/{passenger_id}/remove/")
def remove_from_basket(passenger_id: str, req: BasketPositionRemove):
    product = products_repo.by_id(req.product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    baskets_manager.remove_from_basket(passenger_id, product)


@router.post("/{passenger_id}/checkout/")
def checkout_basket(passenger_id: str) -> OrderDetails:
    pass