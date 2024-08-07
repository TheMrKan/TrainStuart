import serial
from multiprocessing import Process, Manager, Event
from typing import Optional, List
from utils.cancelations import CancellationToken, await_event
from robot.config import instance as config
from robot.hardware.serial_process import SharedProtocol, begin, Command, Request


process: Process
shared: SharedProtocol
on_state_changed: Event
on_confirmation_received: Event
on_completion_received: Event
on_response_received: Event
on_message_sent: Event
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
    global on_message_sent

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
    on_message_sent = Event()
    shared.response_code = None
    shared.response_args = None

    process = Process(target=begin,
                      args=(shared, on_state_changed, on_confirmation_received, on_completion_received, on_response_received, on_message_sent),
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


def send_command(command_code: str,
                 *args: int,
                 _await_confirmation: bool = True,
                 _await_completion: bool = False,
                 completion_timeout: Optional[int] = None,
                 completion_cancellation: Optional[CancellationToken] = None):
    command = Command(command_code, *args)

    on_message_sent.clear()
    on_confirmation_received.clear()
    on_completion_received.clear()

    shared.outgoing_message = command
    on_message_sent.wait()
    on_message_sent.clear()

    if _await_confirmation:
        await_confirmation()

    if _await_completion:
        await_completion(completion_timeout, completion_cancellation)


def send_request(request_code: str,
                 *args: int,
                 timeout: Optional[int] = None,
                 cancellation: Optional[CancellationToken] = None) -> List[int]:
    request = Request(request_code, *args)

    on_message_sent.clear()
    on_response_received.clear()
    shared.response_code = None
    shared.response_args = None

    shared.outgoing_message = request
    on_message_sent.wait()
    on_message_sent.clear()

    return await_response(request_code, timeout, cancellation)


def await_confirmation(timeout: Optional[float] = None, cancellation: Optional[CancellationToken] = None):
    await_event(on_confirmation_received, timeout, cancellation)
    on_confirmation_received.clear()


def await_completion(timeout: Optional[float] = None, cancellation: Optional[CancellationToken] = None):
    await_event(on_completion_received, timeout, cancellation)
    on_completion_received.clear()


def await_response(code: str, timeout: Optional[float] = None, cancellation: Optional[CancellationToken] = None) -> list:
    wrong_left = 3
    while wrong_left:
        await_event(on_response_received, timeout, cancellation)
        if shared.response_code != code:
            wrong_left -= 1
            continue
        on_response_received.clear()
        return shared.response_args or []
    raise RuntimeError("Received several responses with wrong codes")
