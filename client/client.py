import socketio

sio = socketio.Client(logger=True, engineio_logger=True)


@sio.event
def connect():
    print("Connexion ouverte")


@sio.event
def connect_error(data):
    print("La connexion a échoué")


@sio.event
def disconnect():
    print("Connexion fermée")


@sio.event
def command(data):
    print("Commande reçue:", data)


if __name__ == '__main__':
    sio.connect('http://127.0.0.1:5000')
    sio.wait()
