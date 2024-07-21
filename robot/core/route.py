from datetime import datetime, timedelta
from robot.config import instance as config


start_time: datetime
departure_time: datetime


def initialize():
    global start_time
    global departure_time
    start_time = datetime.now()
    departure_time = start_time + timedelta(seconds=config.route.boarding_duration)


def is_boarding_finished():
    return datetime.now() >= departure_time
    
    
