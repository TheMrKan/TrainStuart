from threading import Event
from typing import Optional
import time


class CancellationToken:
    cancellation_event: Event

    def __init__(self, event: Optional[Event] = None):
        self.cancellation_event = event or Event()

    def cancel(self):
        self.cancellation_event.set()

    @property
    def is_cancelled(self):
        return self.cancellation_event.is_set()

    def __bool__(self):
        return self.is_cancelled


def sleep(secs: float, cancellation: Optional[CancellationToken] = None):
    if cancellation:
        if cancellation.cancellation_event.wait(timeout=secs):
            raise InterruptedError
    else:
        time.sleep(secs)


def await_event(event: Event, timeout: Optional[float] = None, cancellation: Optional[CancellationToken] = None, step: float = 0.1) -> bool:
    if cancellation is None:
        return event.wait(timeout)
    
    start = time.time()
    if timeout is not None:
        if timeout <= 0:
            return False
        while True:
            if cancellation.cancellation_event.is_set():
                raise InterruptedError
            t = time.time() - start
            if t >= timeout:
                return False
            if event.wait(timeout=min(step, timeout - t)):
                return True
    else:
        while True:
            if cancellation.cancellation_event.is_set():
                raise InterruptedError
            if event.wait(timeout=step):
                return True
