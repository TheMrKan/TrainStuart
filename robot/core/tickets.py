import time


class TicketInfo:
    number: str
    owner_name: str
    owner_passport: str
    carriage_num: int    # номер вагона
    seat_num: int    # номер места


class TicketsRepository:
    number_map = {}
    name_map = {}
    passport_map = {}

    @classmethod
    def load(cls):
        time.sleep(1)    # запрос к серверу с билетами
    
    @classmethod
    def get_by_number(cls, ticket_number: str) -> TicketInfo | None:
        return cls.number_map.get(ticket_number, None)

    @classmethod
    def get_by_name(cls, full_name: str) -> TicketInfo | None:
        return cls.name_map.get(full_name, None)

    @classmethod
    def get_by_passport(cls, passport_number: str) -> TicketInfo | None:
        return cls.passport_map.get(passport_number, None)
