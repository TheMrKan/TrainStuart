from robot.config import instance as config
import robot.hardware


def build():
    if config.hardware.dummy_robot:
        from robot.hardware import robot_dummy
        robot.hardware.robot_interface = robot_dummy
