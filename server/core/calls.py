from dataclasses import dataclass
import datetime

# ID кнопки : номер места
BUTTONS = {
    1: 2,
    2: 4
}


@dataclass
class Call:
    seat: int
    created: datetime.datetime


active_calls = list()


def call_to_button(button_id: int):
    seat = BUTTONS[button_id]
    call_to_seat(seat)


def call_to_seat(seat: int):
    if seat in active_calls:
        return

    active_calls.append(seat)
    print(f"Registered new call to seat {seat}")


def mark_call_completed(seat: int):
    if seat in active_calls:
        active_calls.remove(seat)


