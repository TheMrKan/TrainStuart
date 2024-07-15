from server.core.baskets.models import PassengerBasket


baskets: dict[str, PassengerBasket] = {}


def by_id(passenger_id: str) -> PassengerBasket:
    return baskets.get(passenger_id, {})


def add(basket: PassengerBasket):
     baskets[basket.passenger_id] = basket


def remove(passenger_id: str):
     del baskets[passenger_id]