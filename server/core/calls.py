from dataclasses import dataclass
import datetime

# ID кнопки : номер места
BUTTONS = {
    1: 2,
    2: 4
}


active_calls = set()


def call_to_button(button_id: int):
    seat = BUTTONS[button_id]
    call_to_seat(seat)


def call_to_seat(seat: int):
    if seat in active_calls:
        return

    active_calls.add(seat)
    print(f"Registered new call to seat {seat}")



