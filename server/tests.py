from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)


def test_update_basket():
    response = client.post("/baskets/robot/update/", json={"product_id": "water_still_0,5", "amount": 2})
    assert response.status_code == 200

    response = client.post("/baskets/robot/update/", json={"product_id": "unknown_product", "amount": 1})
    assert response.status_code == 404

    response = client.post("/baskets/robot/update/", json={"product_id": "cola", "amount": 5})
    assert response.status_code == 409

    response = client.get("/baskets/robot/")
    assert response.json() == {'positions': [{'product_id': 'water_still_0,5', 'amount': 2, 'total_price': 100.0}], 'total_price': 100.0}

if __name__ == "__main__":
    test_update_basket()
