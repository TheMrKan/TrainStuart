import time
from utils.collections import first_or_default
from dataclasses import dataclass


@dataclass
class TicketInfo:
    number: str
    owner_name: str
    owner_passport: str
    carriage_num: int    # номер вагона
    seat_num: int    # номер места

    def __str__(self):
        return f"{self.number} {self.owner_name} ({self.carriage_num} - {self.seat_num})"
    
    def __repr__(self):
        return self.__str__()


class TicketsRepository:
    __tickets = []

    @classmethod
    def load(cls):
        time.sleep(1)    # запрос к серверу с билетами

        cls.__load_ticket(TicketInfo("1", "ИВАНОВ ИВАН ИВАНОВИЧ", "6019767612", 1, 5))

    @classmethod
    def __load_ticket(cls, ticket: TicketInfo):
        cls.__tickets.append(ticket)
    
    @classmethod
    def get_by_number(cls, ticket_number: str) -> TicketInfo | None:
        return first_or_default(cls.__tickets, lambda t: t.number == ticket_number)

    @classmethod
    def get_by_name(cls, full_name: str) -> TicketInfo | None:
        return first_or_default(cls.__tickets, lambda t: t.owner_name == full_name)

    @classmethod
    def get_by_passport(cls, passport_number: str) -> TicketInfo | None:
        return first_or_default(cls.__tickets, lambda t: t.owner_passport == passport_number)
