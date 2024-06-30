from threading import Event
from typing import Optional
import time


class CancellationToken:
    cancellation_event: Event

    def __init__(self):
        self.cancellation_event = Event()

    def cancel(self):
        self.cancellation_event.set()


def sleep(secs: float, cancellation: Optional[CancellationToken] = None):
    if cancellation:
        if cancellation.cancellation_event.wait(timeout=secs):
            raise InterruptedError
    else:
        time.sleep(secs)


def await_event(event: Event, timeout: Optional[float] = None, cancellation: Optional[CancellationToken] = None, step: float = 0.1):
    start = time.time()
    if timeout is not None:
        while True:
            if cancellation.cancellation_event.is_set():
                raise InterruptedError
            t = time.time() - start
            if t >= timeout or event.wait(timeout=min(step, timeout - t)):
                break
    else:
        while True:
            if cancellation.cancellation_event.is_set():
                raise InterruptedError
            if event.wait(timeout=step):
                break
