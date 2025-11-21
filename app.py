from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.utils import secure_filename
import os, sqlite3, qrcode
from datetime import datetime, timedelta

# --------------------------------
# APP CONFIGURATION
# --------------------------------
app = Flask(__name__)
app.secret_key = "dropvault_secure_key"

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['QR_FOLDER'] = 'static/qr'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['QR_FOLDER'], exist_ok=True)

DB_FILE = "database.db"

# --------------------------------
# DATABASE INITIALIZATION
# --------------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        theme TEXT DEFAULT 'light',
        notifications TEXT DEFAULT 'all'
    )''')

    # Files table
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
# AUTH ROUTES
# --------------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id, name FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            flash("Login successful ✅")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials ❌")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            conn.commit()
            flash("Registration successful 🎉 Please log in.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered ❌")
        finally:
            conn.close()
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully ✅")
    return redirect(url_for("login"))


# --------------------------------
# DASHBOARD
# --------------------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT filename, token, expiry, qr_path FROM files WHERE user_id=?", (session["user_id"],))
    rows = c.fetchall()
    conn.close()

    files = []
    for r in rows:
        files.append({
            "filename": r[0],
            "expiry": r[2],
            "link": f"/shared/{r[1]}",
            "token": r[1],
            "qr": r[3]
        })

    storage = {"used": 1.2, "total": 10, "percent_used": 12}
    recent_files = [f["filename"] for f in files[-3:]]
    shared_count = len(files)

    return render_template("dashboard.html", 
                           user_name=session.get("user_name"),
                           storage=storage,
                           recent_files=recent_files,
                           shared_count=shared_count,
                           files=files)



# --------------------------------
# UPLOAD
# --------------------------------
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files["file"]
        expiry_hours = int(request.form.get("expiry", 24))  # default 24 hrs

        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            expiry_time = datetime.now() + timedelta(hours=expiry_hours)
            token = f"{int(datetime.now().timestamp())}_{filename.replace(' ', '_')}"
            link = f"http://127.0.0.1:5000/shared/{token}"

            # Generate QR code
            qr_img = qrcode.make(link)
            qr_path = os.path.join(app.config['QR_FOLDER'], f"{token}.png")
            qr_img.save(qr_path)

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO files (user_id, filename, token, expiry, qr_path) VALUES (?, ?, ?, ?, ?)",
                      (session["user_id"], filename, token, expiry_time, qr_path))
            conn.commit()
            conn.close()

            flash("File uploaded successfully ✅")
            return redirect(url_for("myfiles"))

    return render_template("upload.html")


# --------------------------------
# MY FILES
# --------------------------------
@app.route("/myfiles")
def myfiles():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT filename, token, expiry, qr_path FROM files WHERE user_id=?", (session["user_id"],))
    files = []
    for row in c.fetchall():
        expiry = datetime.fromisoformat(row[2])
        files.append({
            "filename": row[0],
            "expiry": expiry.strftime("%Y-%m-%d %H:%M"),
            "link": f"/shared/{row[1]}",
            "qr": row[3]
        })
    conn.close()

    return render_template("myfiles.html", files=files)


# --------------------------------
# SHARED FILES
# --------------------------------
@app.route("/shared")
def shared_files():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT filename, token, expiry, qr_path FROM files WHERE user_id=?", (session["user_id"],))
    rows = c.fetchall()
    conn.close()

    files = []
    for r in rows:
        expiry = datetime.fromisoformat(r[2])
        remaining = expiry - datetime.now()
        files.append({
            "filename": r[0],
            "link": f"http://127.0.0.1:5000/shared/{r[1]}",
            "expiry": expiry.strftime("%Y-%m-%d %H:%M:%S"),
            "remaining": str(remaining).split('.')[0],
            "qr": r[3]
        })

    return render_template("shared.html", files=files)


@app.route("/shared/<token>")
def shared_download(token):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT filename, expiry FROM files WHERE token=?", (token,))
    row = c.fetchone()
    conn.close()

    if not row:
        return "File not found ❌"

    expiry = datetime.fromisoformat(row[1])
    if datetime.now() > expiry:
        return "This link has expired ⏰"

    return send_from_directory(app.config['UPLOAD_FOLDER'], row[0], as_attachment=True)


# --------------------------------
# SETTINGS & PROFILE MANAGEMENT
# --------------------------------
def get_current_user():
    if "user_id" not in session:
        return None
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, email, theme, notifications FROM users WHERE id=?", (session["user_id"],))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "username": row[0],
            "email": row[1],
            "theme": row[2],
            "notifications": row[3],
            "twofa_enabled": False
        }
    return None


@app.route("/settings")
def settings():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = get_current_user()

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM files WHERE user_id=?", (session["user_id"],))
    count = c.fetchone()[0]
    conn.close()

    storage = {
        "used": count * 10,
        "total": 1000,
        "percent_used": min((count * 10 / 1000) * 100, 100)
    }

    return render_template("settings.html", user=user, storage=storage)


@app.route("/update_profile", methods=["POST"])
def update_profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    username = request.form.get("username")
    email = request.form.get("email")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET name=?, email=? WHERE id=?", (username, email, session["user_id"]))
    conn.commit()
    conn.close()

    flash("Profile updated successfully ✅")
    return redirect(url_for("settings"))


@app.route("/update_password", methods=["POST"])
def update_password():
    if "user_id" not in session:
        return redirect(url_for("login"))

    password = request.form.get("password")
    if not password:
        flash("Please enter a new password ❌")
        return redirect(url_for("settings"))

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET password=? WHERE id=?", (password, session["user_id"]))
    conn.commit()
    conn.close()

    flash("Password updated successfully 🔒")
    return redirect(url_for("settings"))


@app.route("/update_preferences", methods=["POST"])
def update_preferences():
    if "user_id" not in session:
        return redirect(url_for("login"))

    theme = request.form.get("theme")
    notifications = request.form.get("notifications")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET theme=?, notifications=? WHERE id=?", (theme, notifications, session["user_id"]))
    conn.commit()
    conn.close()

    flash("Preferences updated successfully 🎨")
    return redirect(url_for("settings"))

@app.route("/toggle_2fa", methods=["POST"])
def toggle_2fa():
    """Toggle Two-Factor Authentication for the user"""
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    # (You can store 2FA status in DB; for now, simulate in session)
    session["twofa_enabled"] = not session.get("twofa_enabled", False)
    status = "enabled ✅" if session["twofa_enabled"] else "disabled ❌"
    flash(f"Two-Factor Authentication {status}", "success")
    return redirect(url_for("settings"))



# --------------------------------
# APP RUNNER
# --------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
