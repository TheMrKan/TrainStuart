import serial
from multiprocessing import Process, Manager, Event
from typing import Optional
from utils.cancelations import CancellationToken, await_event
from robot.config import instance as config
from robot.hardware.serial_process import SharedProtocol, begin


process: Process
shared: SharedProtocol
on_state_changed: Event
on_confirmation_received: Event
on_completion_received: Event
on_response_received: Event
manager: Manager


class InterfaceUnavailableError(Exception):
    pass


def setup():
    global process
    global manager
    global shared
    global on_state_changed
    global on_confirmation_received
    global on_completion_received
    global on_response_received

    manager = Manager()
    shared = manager.Namespace()
    shared.serial_name = config.hardware.serial
    if not shared.serial_name:
        raise ValueError("Serial name is not configured")
    shared.is_running = True
    shared.is_connected = False
    shared.exception = None
    on_state_changed = Event()
    on_confirmation_received = Event()
    on_completion_received = Event()
    on_response_received = Event()
    shared.response_code = None
    shared.response_args = None

    process = Process(target=begin,
                      args=(shared, on_state_changed, on_confirmation_received, on_completion_received, on_response_received),
                      name="robot.hardware.serial_process")
    process.start()

    await_event(on_state_changed, timeout=8)
    on_state_changed.clear()

    if shared.is_connected:
        return

    if shared.exception:
        raise InterfaceUnavailableError() from shared.exception
    else:
        raise InterfaceUnavailableError()


def send_command(command_key: str, *args: list, await_confirmation: bool = True, await_completion: bool = False):
    raise NotImplementedError


def request(request_key: str, *args: list) -> list:
    raise NotImplementedError


def await_confirmation(timeout: Optional[float] = None, cancellation: Optional[CancellationToken] = None):
    raise NotImplementedError


def await_response(code: str, timeout: Optional[float] = None, cancellation: Optional[CancellationToken] = None) -> list:
    raise NotImplementedError
