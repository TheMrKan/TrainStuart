import time

from bottle import Bottle, run as run_bottle, static_file, ServerAdapter
from multiprocessing import Event
from threading import Thread


class StoppableServer(ServerAdapter):
    def run(self, handler):
        from wsgiref.simple_server import make_server, WSGIRequestHandler

        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw): pass
            handler_class = QuietHandler
        else:
            handler_class = WSGIRequestHandler

        self.server = make_server(self.host, self.port, handler, handler_class=handler_class)
        self.server.serve_forever(poll_interval=0.1)

    def stop(self):
        self.server.shutdown()


bottle_app: Bottle
http_server: StoppableServer
stop_event: Event
watcher: Thread

STATIC_DIR = "gui/assets/static"
TEMPLATES_DIR = "gui/assets"


def http_static(filename):
    return static_file(filename, root=STATIC_DIR)


def http_page(page):
    return static_file(page + ".html", root=TEMPLATES_DIR)


def run(_stop_event: Event):
    global bottle_app
    global http_server
    global stop_event
    global watcher

    stop_event = _stop_event

    bottle_app = Bottle()
    bottle_app.route('/static/<filename:path>', "GET", http_static)
    bottle_app.route("<page:path>", "GET", http_page)

    watcher = Thread(target=__watcher, name="robot.gui.base.http.watcher", daemon=True)
    watcher.start()

    http_server = StoppableServer(host="robot", port=8000, quite=True)
    run_bottle(bottle_app, server=http_server)


def __watcher():
    while not stop_event.is_set():
        time.sleep(0.5)
    http_server.stop()

