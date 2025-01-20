import time
import logging
import serial
from multiprocessing import Process, Manager, Event
from threading import Thread
from typing import Optional, List
from utils.cancelations import CancellationToken, await_event
from robot.config import instance as config
from robot.hardware.serial_process import SharedProtocol, begin, Command, Request
from pymitter import EventEmitter

logger = logging.getLogger(__name__)


process: Process
shared: SharedProtocol
on_state_changed: Event
on_confirmation_received: Event
on_completion_received: Event
on_response_received: Event
on_message_sent: Event
__on_command_received: Event
manager: Manager
watcher_thread: Thread

on_command = EventEmitter(wildcard=True)


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
    global __on_command_received
    global watcher_thread

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
    shared.outgoing_message = None
    __on_command_received = Event()
    shared.command = None

    process = Process(target=begin,
                      args=(shared, on_state_changed, on_confirmation_received, on_completion_received,
                            on_response_received, __on_command_received, on_message_sent),
                      name="robot.hardware.serial_process")
    process.start()

    await_event(on_state_changed, timeout=8)
    on_state_changed.clear()

    if not shared.is_connected:
        if shared.exception:
            raise InterfaceUnavailableError() from shared.exception
        else:
            raise InterfaceUnavailableError()

    watcher_thread = Thread(target=__watcher, name="robot.hardware.serial_interface.__watcher", daemon=True)
    watcher_thread.start()


def send_command(command_code: str,
                 *args: int,
                 confirmation: bool = True,
                 completion: bool = False,
                 completion_timeout: Optional[int] = None,
                 completion_cancellation: Optional[CancellationToken] = None):
    command = Command(command_code, *args)

    on_message_sent.clear()
    on_confirmation_received.clear()
    on_completion_received.clear()

    shared.outgoing_message = command
    on_message_sent.wait()
    on_message_sent.clear()

    if confirmation:
        await_confirmation()

    if completion:
        await_completion(completion_timeout, completion_cancellation)


def send_request(request_code: str,
                 *args: int,
                 response: Optional[bool] = True,
                 timeout: Optional[int] = None,
                 cancellation: Optional[CancellationToken] = None) -> Optional[List[int]]:
    request = Request(request_code, *args)

    on_message_sent.clear()
    on_response_received.clear()
    shared.response_code = None
    shared.response_args = None

    shared.outgoing_message = request
    on_message_sent.wait()
    on_message_sent.clear()

    if response:
        try:
            return await_response(request_code, timeout, cancellation)
        except InterfaceError as e:
            logger.error(f"Protocol error during request '{request_code}'", exc_info=e)
            return None
        except TimeoutError:
            logger.error(f"Timeout reached ({timeout} seconds) during request '{request_code}'")
            return None
    return None


def await_confirmation(timeout: Optional[float] = None, cancellation: Optional[CancellationToken] = None):
    await_event(on_confirmation_received, timeout, cancellation)
    on_confirmation_received.clear()


def await_completion(timeout: Optional[float] = None, cancellation: Optional[CancellationToken] = None):
    await_event(on_completion_received, timeout, cancellation)
    on_completion_received.clear()


class InterfaceError(Exception):
    def __init__(self, *args):
        super().__init__(*args)


def await_response(code: str, timeout: Optional[float] = None, cancellation: Optional[CancellationToken] = None) -> list:
    wrong_left = 3
    _wrong = []
    while wrong_left:
        is_timeout = not await_event(on_response_received, timeout, cancellation)
        if is_timeout:
            raise TimeoutError

        if shared.response_code != code:
            wrong_left -= 1
            _wrong.append(shared.response_code)
            continue
        on_response_received.clear()
        return shared.response_args or []
    raise InterfaceError(f"Received several responses with wrong codes ({_wrong})")


def __watcher():
    while True:
        if __on_command_received.is_set() and shared.command is not None:
            __on_command_received.clear()
            Thread(target=on_command.emit,
                   args=(shared.command.code, *shared.command.args),
                   name=f"Event '{shared.command.code}' from 'robot.hardware.serial_interface.__watcher'").start()
            shared.command = None
        time.sleep(0.1)
