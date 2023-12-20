from flask import Flask
from threading import Thread
import logging

app = Flask('keep_alive')

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


@app.route('/')
def home():
    return "I'm alive"


def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
