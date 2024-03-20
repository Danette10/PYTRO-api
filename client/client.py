import io
import socketio
import pyautogui
import base64
import time
from PIL import Image

sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=2)


@sio.event
def connect():
    print("Connexion ouverte")


@sio.event
def connect_error(data):
    print(f"La connexion a échoué : {data}")


@sio.event
def disconnect():
    print("Connexion fermée")


@sio.event
def command(data):
    if data.get('command') == 'screenshot':
        print("Capture d'écran demandée")
        take_and_send_screenshot()
    else:
        print(f"Commande non reconnue: {data}")


def resize_image(image, base_width=1300):
    img = Image.open(image)
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

        while not sio.connected:
            print("En attente de connexion pour envoyer la capture d'écran...")
            time.sleep(1)
        sio.emit('screenshot_response', {'screenshot': screenshot_encoded})
        print("Capture d'écran envoyée")
    except Exception as e:
        print(f"Erreur lors de la prise ou de l'envoi de la capture d'écran : {e}")


if __name__ == '__main__':
    try:
        # sio.connect('http://127.0.0.1:5000')
        sio.connect('http://192.168.220.129:5000')
        sio.wait()
    except KeyboardInterrupt:
        print("Arrêt du client sur demande de l'utilisateur.")
        sio.disconnect()
