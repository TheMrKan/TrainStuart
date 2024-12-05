from fastapi import Request
from server.core import passengers


def get_passenger(request: Request):
    ticket = request.cookies.get("Ticket")
    if ticket:
        return passengers.by_ticket(ticket).id

    return "robot"    # TODO: реализовать идентификацию робота
