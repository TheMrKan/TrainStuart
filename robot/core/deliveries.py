import logging
from typing import Optional
from dataclasses import dataclass

from robot.core import server
from robot.hardware.robot_interface import RobotContainer

logger = logging.getLogger(__name__)

has_new_delivery = False


def initialize():
    server.events.on("updated_deliveries", on_deliveries_updated)

    deliveries = server.get_deliveries()
    if any(deliveries):
        global has_new_delivery
        has_new_delivery = True


def on_deliveries_updated(has_new: bool):
    global has_new_delivery
    has_new_delivery = has_new
    if not has_new:
        return

    logger.info("Received deliveries update")


@dataclass
class Delivery:
    id: str
    container: RobotContainer
    seat: int


def take_delivery(force_update: bool = True) -> Optional[Delivery]:
    global has_new_delivery
    if not force_update and not has_new_delivery:
        return None

    deliveries = server.get_deliveries()
    has_new_delivery = len(deliveries) >= 2
    if not any(deliveries):
        return None

    selected: server.RequestedDelivery = max(deliveries, key=lambda d: d["priority"])
    server.take_delivery(selected["id"])
    logger.info("Take delivery: %s", selected)

    return Delivery(selected["id"], RobotContainer.SMALL_FRONT, selected["seat"])


def complete_delivery(delivery: Delivery):
    global has_new_delivery
    server.complete_delivery(delivery.id)

    deliveries = server.get_deliveries()
    has_new_delivery = any(deliveries)

