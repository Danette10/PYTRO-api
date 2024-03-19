import os
from dotenv import load_dotenv
from flask_socketio import SocketIO, emit
from flask import Flask, jsonify, request

BASE_API_URL = '/api/v1'

if os.environ.get('ENV') != 'production':
    load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app)


# ROUTES
@app.route('/api/v1/command', methods=['POST'])
def handle_command():
    command_data = request.json
    socketio.emit('command', command_data)
    return {'status': 'success'}, 200


if __name__ == '__main__':
    if os.environ.get('ENV') == 'production':
        socketio.run(app, host='0.0.0.0', port=5000)
    else:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
