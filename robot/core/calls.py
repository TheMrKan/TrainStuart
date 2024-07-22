import robot.core.server as server


def initialize():
    server.events.on("updated_calls", on_calls_updated)


def on_calls_updated():
    print("Calls updated!")