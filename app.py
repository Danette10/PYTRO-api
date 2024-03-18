import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request

BASE_API_URL = '/api/v1'

if os.environ.get('ENV') != 'production':
    load_dotenv()

app = Flask(__name__)

# ROUTES


if __name__ == '__main__':
    if os.environ.get('ENV') == 'production':
        app.run()
    else:
        app.run(host='0.0.0.0', port=8080, debug=True)
