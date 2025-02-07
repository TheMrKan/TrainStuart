from robot.core.navigation.passenger_zone import PassengerZoneController


class VendingZoneController(PassengerZoneController):

    MOVING_HEAD_Y = 0

    def __init__(self):
        super().__init__()

