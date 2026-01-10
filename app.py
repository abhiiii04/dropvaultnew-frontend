from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
import os
import logging
import uuid
import traceback


# FLASK FRONTEND CONFIG (Render)

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)
app.secret_key = "dropvault_frontend_key"

# --- error logging ----
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
log_path = os.path.join(LOG_DIR, 'error.log')
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.FileHandler(log_path), logging.StreamHandler()])


@app.errorhandler(Exception)
def handle_uncaught_exceptions(e):
    """Log uncaught exceptions with a unique id and return minimal info to client.

    This helps debugging without exposing full traceback to users in production.
    """
    err_id = uuid.uuid4().hex
    tb = traceback.format_exc()
    logging.error('Error id %s: %s', err_id, tb)
    # Return a short message including the error id so you can find the traceback in logs
    return (f"Internal Server Error\nError id: {err_id}"), 500



# FRONTEND PAGE ROUTES (TEMPLATES)

@app.route("/")
def landing():
    return render_template("landing.html")  

@app.route("/login")
def login_page():
    return render_template("login.html")  

@app.route("/register")
def register_page():
    return render_template("register.html")  

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")
    

@app.route("/__debug_dashboard")
def debug_dashboard():
    return "OK: dashboard route reachable"

@app.route("/upload")
def upload_page():
    return render_template("upload.html")

@app.route("/myfiles")
def files_page():
    return render_template("myfiles.html")

@app.route("/shared")
def shared_page():
    return render_template("shared.html")

@app.route("/trash")
def trash_page():
    return render_template("trash.html")

@app.route("/settings")
def settings_page():
    return render_template("settings.html")


# STATIC FILES (needed for images, css, js)

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


# RUN APP FOR RENDER DEPLOYMENT

if __name__ == "__main__":
    from waitress import serve
    import os
    port = int(os.environ.get("PORT", 5000))  
    serve(app, host="0.0.0.0", port=port)
