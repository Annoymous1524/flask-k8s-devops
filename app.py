from flask import Flask, jsonify, render_template_string
import os
import time
from datetime import datetime
import mysql.connector

app = Flask(__name__)

# Start time
start_time = time.time()

# Config
VERSION = os.getenv("VERSION", "dev")
POD_NAME = os.getenv("HOSTNAME", "local")
DB_HOST = os.getenv("DB_HOST", "mariadb")

# ----------------------------------------
# Simple DB check
# ----------------------------------------
def check_db():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user="root",
            password="",
            database="dashboard",
            connect_timeout=2
        )
        conn.close()
        return "🟢 OK"
    except Exception as e:
        return f"🔴 ERROR"

# ----------------------------------------
# API endpoint (used by frontend)
# ----------------------------------------
@app.route("/api/live")
def live():
    return jsonify({
        "pod_name": POD_NAME,
        "version": VERSION,
        "git_hash": "local",
        "db_status": check_db(),
        "uptime": round(time.time() - start_time, 1),
        "timestamp": datetime.now().isoformat()
    })

# ----------------------------------------
# UI
# ----------------------------------------
@app.route("/")
def home():
    return render_template_string("""
    <html>
    <head><title>Simple Dashboard</title></head>
    <body style="font-family:sans-serif;text-align:center;padding:40px;">
        <h1>🔥 Simple Dashboard</h1>
        <div id="data">Loading...</div>

        <script>
        async function load() {
            const res = await fetch('/api/live');
            const data = await res.json();

            document.getElementById('data').innerHTML = `
                <p><b>Pod:</b> ${data.pod_name}</p>
                <p><b>Version:</b> ${data.version}</p>
                <p><b>DB:</b> ${data.db_status}</p>
                <p><b>Uptime:</b> ${data.uptime}s</p>
                <p><b>Time:</b> ${new Date(data.timestamp).toLocaleTimeString()}</p>
            `;
        }

        setInterval(load, 3000);
        load();
        </script>
    </body>
    </html>
    """)

# ----------------------------------------
# Run
# ----------------------------------------
if __name__ == "__main__":
    print(f"🌟 Simple Dashboard starting on :5000")
    app.run(host="0.0.0.0", port=5000)
