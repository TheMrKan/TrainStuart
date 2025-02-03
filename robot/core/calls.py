from typing import List
import logging

import robot.core.server as server

logger = logging.getLogger(__name__)

active_calls = set()


def initialize():
    server.events.on("updated_calls", on_calls_updated)


def on_calls_updated(new_calls: List[int]):
    active_calls.update(*new_calls)
    logger.info(f"New calls received: {new_calls}")