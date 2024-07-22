from datetime import datetime, timedelta
from robot.config import instance as config


start_time: datetime
departure_time: datetime
service_finish_time: datetime


def initialize():
    global start_time
    global departure_time
    global service_finish_time
    start_time = datetime.now()
    departure_time = start_time + timedelta(seconds=config.route.boarding_duration)
    service_finish_time = departure_time + timedelta(seconds=config.route.service_duration)


def is_boarding_finished():
    return datetime.now() >= departure_time


def is_service_finished():
    return datetime.now() >= service_finish_time
    
    
