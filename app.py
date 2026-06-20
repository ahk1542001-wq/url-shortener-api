import sqlite3
import string
import random
from flask import Flask, request, jsonify, redirect
import re

app = Flask(__name__)
DB_NAME = 'shortener.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_code TEXT UNIQUE NOT NULL,
            original_url TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def is_valid_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

@app.route('/api/shorten', methods=['POST'])
def shorten_url():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "URL is required in the JSON body"
            }
        }), 400

    original_url = data['url']
    if not is_valid_url(original_url):
        return jsonify({
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid URL format"
            }
        }), 400

    short_code = generate_short_code()

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Ensure uniqueness
    while True:
        c.execute('SELECT id FROM urls WHERE short_code = ?', (short_code,))
        if not c.fetchone():
            break
        short_code = generate_short_code()
    
    c.execute('INSERT INTO urls (short_code, original_url) VALUES (?, ?)', (short_code, original_url))
    conn.commit()
    conn.close()

    return jsonify({
        "short_code": short_code,
        "original_url": original_url
    }), 201

@app.route('/<code>', methods=['GET'])
def redirect_url(code):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT original_url FROM urls WHERE short_code = ?', (code,))
    result = c.fetchone()
    conn.close()

    if result:
        return redirect(result[0], code=302)
    else:
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": "Short code not found"
            }
        }), 404

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
