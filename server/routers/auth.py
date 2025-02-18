from fastapi import Request, APIRouter, Response, status
from server.core import passengers


router = APIRouter(prefix="/auth")


def get_passenger(request: Request):

    ticket = request.cookies.get("Ticket")
    if ticket:
        pas = passengers.by_ticket(ticket)
        print(f"Got passenger: {pas.name}")
        return pas.id

    return "robot"    # TODO: реализовать идентификацию робота


@router.post("/as/")
def auth_as(response: Response, ticket: str):
    if ticket:
        print(f"Authenticated as {passengers.by_ticket(ticket).name}")
        response.set_cookie(key="Ticket", value=ticket, max_age=600)
    else:
        print(f"Deauthenticated")
        response.delete_cookie(key="Ticket")
    return status.HTTP_200_OK
