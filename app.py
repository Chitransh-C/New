from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import datetime
import os

app = Flask(__name__)
CORS(app)

DB_NAME = "atm.db"

def connect_db():
    return sqlite3.connect(DB_NAME)

@app.route('/')
def home():
    return "ATM Backend with SQLite is running!"

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data.get('name')
    pin = data.get('pin')
    balance = data.get('balance', 0)

    if not name or not pin:
        return jsonify({'status': 'error', 'message': 'Name and PIN required'}), 400

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE pin = ?", (pin,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'status': 'error', 'message': 'PIN already exists'}), 409

    cursor.execute("INSERT INTO users (name, pin, balance) VALUES (?, ?, ?)", (name, pin, balance))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Account created successfully'})

@app.route('/debug/users')
def debug_users():
    try:
        conn = sqlite3.connect('atm.db')
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, name, pin, balance FROM users")
        rows = cursor.fetchall()
        conn.close()
        return jsonify({'status': 'success', 'users': rows})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
@app.route('/debug/tables')
def debug_tables():
    conn = sqlite3.connect('atm.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    conn.close()
    return jsonify({'tables': tables})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    pin = data.get('pin')
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, name, balance FROM users WHERE pin = ?", (pin,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({
            'status': 'success',
            'user_id': user[0],
            'name': user[1],
            'balance': user[2]
        })
    else:
        return jsonify({'status': 'error', 'message': 'Invalid PIN'}), 404

@app.route('/balance/<pin>', methods=['GET'])
def get_balance(pin):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE pin = ?", (pin,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return jsonify({'status': 'success', 'balance': result[0]})
    else:
        return jsonify({'status': 'error', 'message': 'PIN not found'}), 404
def initialize_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create users table if not exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        pin TEXT NOT NULL UNIQUE,
        balance REAL DEFAULT 0
    )
    """)

    # Create transactions table if not exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """)

    conn.commit()
    conn.close()




@app.route('/deposit', methods=['POST'])
def deposit():
    data = request.get_json()
    pin = data.get('pin')
    amount = data.get('amount')

    if not pin or amount is None:
        return jsonify({'status': 'error', 'message': 'PIN and amount required'}), 400

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, balance FROM users WHERE pin = ?", (pin,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Invalid PIN'}), 404

    user_id = result[0]
    new_balance = result[1] + amount

    cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO transactions (user_id, type, amount, timestamp) VALUES (?, ?, ?, ?)",
                   (user_id, 'Deposit', amount, timestamp))

    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'balance': new_balance})

@app.route('/withdraw', methods=['POST'])
def withdraw():
    data = request.get_json()
    pin = data.get('pin')
    amount = data.get('amount')

    if not pin or amount is None:
        return jsonify({'status': 'error', 'message': 'PIN and amount required'}), 400

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, balance FROM users WHERE pin = ?", (pin,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Invalid PIN'}), 404

    user_id = result[0]
    current_balance = result[1]

    if amount > current_balance:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Insufficient balance'}), 400

    new_balance = current_balance - amount
    cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO transactions (user_id, type, amount, timestamp) VALUES (?, ?, ?, ?)",
                   (user_id, 'Withdrawal', amount, timestamp))

    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'balance': new_balance})

@app.route('/history/<pin>', methods=['GET'])
def history(pin):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE pin = ?", (pin,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Invalid PIN'}), 404

    user_id = user[0]
    cursor.execute("SELECT type, amount, timestamp FROM transactions WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    records = cursor.fetchall()
    conn.close()

    return jsonify({'status': 'success', 'transactions': records})

if __name__ == '__main__':
    initialize_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
