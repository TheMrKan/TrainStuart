import serial
from multiprocessing import Event
from typing import Protocol
import traceback


class SharedProtocol(Protocol):
    serial_name: str
    is_running: bool
    is_connected: bool
    exception: Exception | None
    response_code: str | None
    response_args: list[int] | None


shared: SharedProtocol
connection: serial.Serial
on_state_changed: Event
on_confirmation_received: Event
on_completion_received: Event
on_response_received: Event


def begin(_shared: SharedProtocol, _on_state_changed, _on_confirmation_received, _on_completion_received, _on_response_received):
    global shared
    global connection
    global on_state_changed
    global on_confirmation_received
    global on_completion_received
    global on_response_received

    on_state_changed = _on_state_changed
    on_confirmation_received = _on_confirmation_received
    on_completion_received = _on_completion_received
    on_response_received = _on_response_received

    shared = _shared
    connection = None
    try:
        connection = serial.Serial(shared.serial_name, 115200, timeout=5)
        shared.is_connected = True
    except Exception as e:
        shared.exception = e

    on_state_changed.set()

    if connection:
        loop()


def loop():
    global shared
    global connection

    while shared.is_running and connection.is_open:
        try:
            line = read_serial()

            if try_handle_confirmation(line):
                continue

            if try_handle_completion(line):
                continue

            if is_response(line):
                handle_response(line)
        except:
            traceback.print_exc()


def read_serial() -> str:
    bdata = connection.readline()
    return bdata.decode().strip()


def try_handle_confirmation(line: str) -> bool:
    if line != "+":
        return False

    on_confirmation_received.set()
    return True


def try_handle_completion(line: str) -> bool:
    if line != "OK":
        return False

    on_completion_received.set()
    return True


def is_response(line: str):
    return line.startswith("!")


def handle_response(line: str):
    line = line[1:]    # убираем !
    splitted = line.split(" ")

    code = splitted[0]
    if len(splitted) > 1:
        args = list(map(int, splitted[1:]))
    else:
        args = []

    shared.response_code = code
    shared.response_args = args
    on_response_received.set()
