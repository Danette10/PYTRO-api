from flask import Flask, redirect, url_for, render_template, request
from pynput.keyboard import Key, Listener
import webbrowser
import threading

current_keys = []
trigger_words = {
    'facebook': 'http://127.0.0.1:5000/facebook',
    'twitter': 'http://127.0.0.1:5000/twitter',
    'instagram': 'http://127.0.0.1:5000/instagram'
}
page_opened_recently = False  # Flag to control page opening

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


threading.Thread(target=start_listener).start()
