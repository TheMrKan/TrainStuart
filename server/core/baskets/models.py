from dataclasses import dataclass


@dataclass
class PassengerBasket:
    passenger_id: str
    positions: dict[str, int]