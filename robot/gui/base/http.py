import time

from bottle import Bottle, run as run_bottle, static_file, ServerAdapter
from threading import Thread


bottle_app: Bottle
watcher: Thread

STATIC_DIR = "gui/assets/static"
TEMPLATES_DIR = "gui/assets"


def http_static(filename):
    return static_file(filename, root=STATIC_DIR)


def http_page(page):
    return static_file(page + ".html", root=TEMPLATES_DIR)


def run():
    global bottle_app
    global watcher

    bottle_app = Bottle()
    bottle_app.route('/static/<filename:path>', "GET", http_static)
    bottle_app.route("<page:path>", "GET", http_page)

    bottle_app.run(host="robot", port=8000, quite=False, debug=True)


