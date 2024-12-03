from fastapi import APIRouter
from server.core import calls

router = APIRouter(prefix="/carriage")


@router.post("/call/")
async def call(button_id: int):
    calls.call_to_button(button_id)
    return str(button_id)
