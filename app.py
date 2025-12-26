from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os, sqlite3, qrcode
from datetime import datetime, timedelta

# --------------------------------
# CONFIG
# --------------------------------
app = Flask(__name__)
CORS(app)  # allow frontend to connect
app.secret_key = "dropvault_secure_key"

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['QR_FOLDER'] = 'static/qr'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['QR_FOLDER'], exist_ok=True)

DB_FILE = "database.db"

# --------------------------------
# DB INIT
# --------------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        filename TEXT,
        token TEXT,
        expiry DATETIME,
        qr_path TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    conn.commit()
    conn.close()

init_db()

# --------------------------------
# API: REGISTER
# --------------------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
        conn.commit()
        return jsonify({"success": True, "message": "User registered"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Email already exists"}), 400
    finally:
        conn.close()

# --------------------------------
# API: LOGIN
# --------------------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name FROM users WHERE email=? AND password=?", (email, password))
    user = c.fetchone()
    conn.close()

    if not user:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

    return jsonify({
        "success": True,
        "message": "Login successful",
        "token": str(user[0]),
        "name": user[1]
    }), 200

# --------------------------------
# API: DASHBOARD
# --------------------------------
@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    user_id = request.headers.get("Authorization")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT filename, token, expiry, qr_path FROM files WHERE user_id=?", (user_id,))
    rows = c.fetchall()
    conn.close()

    files = [{
        "filename": r[0],
        "expiry": r[2],
        "download_url": f"https://dropvault-2.onrender.com/shared/{r[1]}",
        "qr": f"https://dropvault-2.onrender.com/{r[3]}"
    } for r in rows]

    return jsonify({
        "storage": {"used": 1.2, "total": 10, "percent": 12},
        "recent_files": [f["filename"] for f in files[-3:]],
        "shared_count": len(files),
        "files": files
    })

# --------------------------------
# API: UPLOAD
# --------------------------------
@app.route("/api/upload", methods=["POST"])
def api_upload():
    user_id = request.headers.get("Authorization")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    expiry = datetime.now() + timedelta(hours=24)
    token = f"{int(datetime.now().timestamp())}_{filename.replace(' ', '')}"
    share_url = f"https://dropvault-2.onrender.com/shared/{token}"

    qr_img = qrcode.make(share_url)
    qr_path = os.path.join(app.config["QR_FOLDER"], f"{token}.png")
    qr_img.save(qr_path)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO files (user_id, filename, token, expiry, qr_path) VALUES (?, ?, ?, ?, ?)",
              (user_id, filename, token, expiry, qr_path))
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "share_url": share_url,
        "qr_code": f"https://dropvault-2.onrender.com/{qr_path}"
    })

# --------------------------------
# API: SHARED FILES LIST
# --------------------------------
@app.route("/api/shared", methods=["GET"])
def shared_list():
    user_id = request.headers.get("Authorization")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, filename, token, expiry, qr_path FROM files WHERE user_id=?", (user_id,))
    rows = c.fetchall()
    conn.close()

    files = [{
        "id": r[0],
        "filename": r[1],
        "expiry": r[3],
        "share_url": f"/shared/{r[2]}",
        "qr": f"/{r[4]}"
    } for r in rows]

    return jsonify({"shared": files})

# --------------------------------
# DOWNLOAD SHARED FILE
# --------------------------------
@app.route("/shared/<token>")
def shared_download(token):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT filename, expiry FROM files WHERE token=?", (token,))
    row = c.fetchone()
    conn.close()

    if not row:
        return "File not found ❌"

    if datetime.now() > datetime.fromisoformat(row[1]):
        return "This link has expired ⏰"

    return send_from_directory("uploads", row[0], as_attachment=True)

# --------------------------------
# DEPLOY
# --------------------------------
from waitress import serve
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render gives PORT automatically
    serve(app, host="0.0.0.0", port=port)

