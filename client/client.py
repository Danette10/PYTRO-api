import io
import socketio
import pyautogui
import base64
import time
from PIL import Image

sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=2)


def log_event(message):
    print(message)


@sio.event
def connect():
    log_event("Connection opened")


@sio.event
def connect_error(data):
    log_event(f"Connection failed: {data}")


@sio.event
def disconnect():
    log_event("Connection closed")


@sio.event
def command(data):
    command = data.get('command')
    if command == 'screenshot':
        log_event("Screenshot requested")
        take_and_send_screenshot()
    else:
        log_event(f"Unrecognized command: {command}")


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
            log_event("Waiting for connection to send the screenshot...")
            time.sleep(1)
        sio.emit('screenshot_response', {'screenshot': screenshot_encoded})
        log_event("Screenshot sent")
    except Exception as e:
        log_event(f"Error taking or sending the screenshot: {e}")


def main():
    try:
        sio.connect('http://192.168.220.129:5000')
        sio.wait()
    except KeyboardInterrupt:
        log_event("Client stopped by user request.")
        sio.disconnect()


if __name__ == '__main__':
    main()
