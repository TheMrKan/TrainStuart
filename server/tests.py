from fastapi.testclient import TestClient
from server.main import app
from server.routers.models import OrderDetails
import server.core.passengers as passengers
from typing import Callable
from functools import wraps

import signal

# Отключаем signal.set_wakeup_fd для тестирования
signal.set_wakeup_fd = lambda fd: None

ticket = "1"
client = TestClient(app, cookies={"Ticket": ticket})

response = None


def print_failed_assertations(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AssertionError:
            print(response.status_code, response.json())
            raise
    return wrapper


@print_failed_assertations
def test_basket():
    global response
    passenger = passengers.by_ticket(ticket)

    response = client.post(f"/baskets/update/", json={"product_id": "water_still_05", "amount": 2})
    assert response.status_code == 200

    response = client.post(f"/baskets/update/", json={"product_id": "unknown_product", "amount": 1})
    assert response.status_code == 404

    response = client.post(f"/baskets/update/", json={"product_id": "cola", "amount": 5})
    assert response.status_code == 409

    response = client.post(f"/baskets/update/", json={"product_id": "cola", "amount": 1})
    assert response.status_code == 200

    response = client.get(f"/baskets/")

    assert response.json() == {
        'positions': [{
            'product_id': 'water_still_05',
            'amount': 2, 
            'total_price': 100.0
            },
            {
            'product_id': 'cola', 
            'amount': 1, 
            'total_price': 100.0
            }], 
        'total_price': 200.0
        }

    response = client.post(f"/baskets/update/", json={"product_id": "cola", "amount": 0})
    assert response.status_code == 200

    response = client.post(f"/baskets/remove/", json={"product_id": "water_still_05"})
    assert response.status_code == 200

    response = client.get(f"/baskets/")
    assert response.json() == {
        'positions': [], 
        'total_price': 0.0
        }
    

@print_failed_assertations
def test_basket_checkout():
    global response
    passenger = passengers.by_ticket(ticket)

    response = client.post(f"/baskets/checkout/")
    assert response.status_code == 409

    response = client.post(f"/baskets/update/", json={"product_id": "water_still_05", "amount": 2})
    assert response.status_code == 200

    response = client.post(f"/baskets/update/", json={"product_id": "cola", "amount": 1})
    assert response.status_code == 200

    response = client.post(f"/baskets/checkout/")
    assert response.status_code == 200
    assert response.json()["passenger_id"] == passenger.id
    assert response.json()["total_price"] == 200

    order_id = response.json()["id"]
    response = client.post(f"/orders/{order_id}/pay/")
    assert response.status_code == 200

    response = client.get("/delivery/list/")
    deliveries = response.json()
    for d in deliveries:
        del d["id"]
    assert deliveries == [
        {'item_id': 'water_still_05',
         'seat': 1,
         'priority': 1
         }, 
         {'item_id': 'water_still_05',
          'seat': 1,
          'priority': 1}, 
          {'item_id': 'cola', 
           'seat': 1,
           'priority': 1}
    ]

if __name__ == "__main__":
    test_basket()
    test_basket_checkout()
