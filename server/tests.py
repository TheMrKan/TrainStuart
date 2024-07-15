from fastapi.testclient import TestClient
from server.main import app
from server.routers.models import OrderDetails

client = TestClient(app)


def test_basket():
    response = client.post("/baskets/robot/update/", json={"product_id": "water_still_0,5", "amount": 2})
    assert response.status_code == 200

    response = client.post("/baskets/robot/update/", json={"product_id": "unknown_product", "amount": 1})
    assert response.status_code == 404

    response = client.post("/baskets/robot/update/", json={"product_id": "cola", "amount": 5})
    assert response.status_code == 409

    response = client.post("/baskets/robot/update/", json={"product_id": "cola", "amount": 1})
    assert response.status_code == 200

    response = client.get("/baskets/robot/")
    assert response.json() == {
        'positions': [{
            'product_id': 'water_still_0,5', 
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

    response = client.post("/baskets/robot/update/", json={"product_id": "cola", "amount": 0})
    assert response.status_code == 200

    response = client.post("/baskets/robot/remove/", json={"product_id": "water_still_0,5"})
    assert response.status_code == 200

    response = client.get("/baskets/robot/")
    assert response.json() == {
        'positions': [], 
        'total_price': 0.0
        }
    

def test_basket_checkout():
    response = client.post("/baskets/robot/checkout/")
    assert response.status_code == 409

    response = client.post("/baskets/robot/update/", json={"product_id": "water_still_0,5", "amount": 2})
    assert response.status_code == 200

    response = client.post("/baskets/robot/update/", json={"product_id": "cola", "amount": 1})
    assert response.status_code == 200

    response = client.post("/baskets/robot/checkout/")
    assert response.status_code == 200
    assert response.json()["passenger_id"] == "robot"
    assert response.json()["total_price"] == 200

if __name__ == "__main__":
    test_basket()
    test_basket_checkout()
