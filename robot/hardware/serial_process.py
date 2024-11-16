import time

import serial
from multiprocessing import Event
from typing import Protocol, Optional, List, Tuple
import traceback


class Command:
    code: str
    args: Tuple[int]

    def __init__(self, code: str, *args: int):
        self.code = code
        self.args = args

    def __str__(self):
        str_args = ' '.join(map(str, self.args))
        return f"{self.code}{' ' + str_args if str_args else ''}\n"


class Request(Command):
    def __str__(self):
        return "?" + super().__str__()


class SharedProtocol(Protocol):
    serial_name: str
    is_running: bool
    is_connected: bool
    exception: Optional[Exception]
    response_code: Optional[str]
    response_args: Optional[list]
    outgoing_message: Optional[Command]


shared: SharedProtocol
connection: serial.Serial
on_state_changed: Event
on_confirmation_received: Event
on_completion_received: Event
on_response_received: Event
on_message_sent: Event
sending: float = 0


def begin(_shared: SharedProtocol, _on_state_changed, _on_confirmation_received, _on_completion_received, _on_response_received, _on_message_sent):
    global shared
    global connection
    global on_state_changed
    global on_confirmation_received
    global on_completion_received
    global on_response_received
    global on_message_sent

    on_state_changed = _on_state_changed
    on_confirmation_received = _on_confirmation_received
    on_completion_received = _on_completion_received
    on_response_received = _on_response_received
    on_message_sent = _on_message_sent

    shared = _shared
    connection = None
    try:
        connection = serial.Serial(
            port=shared.serial_name,
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
        )
        shared.is_connected = True
    except Exception as e:
        shared.exception = e

    on_state_changed.set()

    if connection:
        loop()


def loop():
    global shared
    global connection
    global sending

    buffer: List[str] = []

    while shared.is_running and connection.is_open:
        try:
            line = read_serial(buffer)
            if line:
                handle_line(line)

            if sending == 0:
                send_outgoing_message()
            elif time.time() - sending > 0.5:
                sending = 0
                send_outgoing_message()

        except:
            traceback.print_exc()
        finally:
            time.sleep(0.02)


def read_serial(buffer: List[str]) -> Optional[str]:
    while connection.in_waiting:
        raw = connection.read()
        char = raw.decode("ascii")
        if char == "\r":
            continue

        if char == "\n":
            line = "".join(buffer)
            buffer.clear()
            return line
        buffer.append(char)


def handle_line(line: str):
    print(f"SERIAL <<< {line}")
    if try_handle_confirmation(line):
        return

    if try_handle_completion(line):
        return

    try_handle_response(line)


def try_handle_confirmation(line: str) -> bool:
    if line != "+":
        return False

    global sending

    sending = 0
    shared.outgoing_message = None

    on_confirmation_received.set()
    return True


def try_handle_completion(line: str) -> bool:
    if line != "OK":
        return False
    print("Completion received")
    on_completion_received.set()
    return True


def try_handle_response(line: str) -> bool:
    if not line.startswith("!"):
        return False

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


def send_outgoing_message():
    global sending
    if not shared.outgoing_message or sending:
        return

    command_str = str(shared.outgoing_message)
    connection.write(command_str.encode("ascii"))
    print(f"SERIAL >>> {command_str}")
    sending = time.time()
    on_message_sent.set()

