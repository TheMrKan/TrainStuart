import logging
from typing import Optional
from dataclasses import dataclass

from robot.core import server

logger = logging.getLogger(__name__)


def initialize():
    server.events.on("updated_deliveries", on_deliveries_updated)


def on_deliveries_updated(has_new: bool):
    if not has_new:
        return

    logger.info("Received deliveries update")
    delivery = take_delivery()
    print(delivery)


@dataclass
class Delivery:
    container: int
    seat: int


def take_delivery() -> Optional[Delivery]:
    deliveries = server.get_deliveries()
    if not deliveries:
        return None

    selected: server.RequestedDelivery = max(deliveries, key=lambda d: d["priority"])
    server.take_delivery(selected["id"])

    return Delivery(0, selected["seat"])

