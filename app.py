from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

users = {}

@app.route('/')
def home():
    return "ATM Backend is running!"

@app.route('/signup', methods=['POST', 'OPTIONS'])
def signup():
    if request.method == 'OPTIONS':
        response = app.make_response('')
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response

    data = request.get_json()
    name = data.get('name')
    pin = data.get('pin')

    if not name or not pin:
        return jsonify({'status': 'error', 'message': 'Name and PIN required'}), 400

    if pin in users:
        return jsonify({'status': 'error', 'message': 'PIN already exists'}), 409

    users[pin] = {
        'name': name,
        'balance': 0,
        'history': ['Account created']
    }

    return jsonify({'status': 'success', 'message': 'Account created successfully'})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

