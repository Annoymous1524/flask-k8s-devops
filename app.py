from flask import Flask, jsonify
import mysql.connector
import os
import subprocess
from datetime import datetime
import threading
import time

app = Flask(__name__)

# Config
VERSION = os.getenv("VERSION", "dev")
GIT_HASH = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                         capture_output=True, text=True).stdout.strip() if os.path.exists('.git') else "local"
POD_NAME = os.getenv("HOSTNAME", os.getenv("POD_NAME", "localhost"))

# Live data store
live_data = {
    "version": VERSION,
    "git_hash": GIT_HASH,
    "pod_name": POD_NAME,
    "timestamp": datetime.now().isoformat(),
    "db_status": "checking",
    "uptime": 0,
    "requests": 0
}

def update_live_data():
    """Background thread for live updates"""
    while True:
        try:
            # DB check
            db = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", "test"),
                connect_timeout=3
            )
            live_data["db_status"] = "🟢 OK"
            db.close()
        except:
            live_data["db_status"] = "🔴 DOWN"
        
        live_data["timestamp"] = datetime.now().isoformat()
        live_data["uptime"] = round(time.time() - start_time, 1)
        time.sleep(5)  # Update every 5s

start_time = time.time()
threading.Thread(target=update_live_data, daemon=True).start()

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>📊 Live Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 500;
        }
        .card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 2.5rem;
            max-width: 500px;
            width: 90vw;
            box-shadow: 0 25px 45px rgba(0,0,0,0.2);
            border: 1px solid rgba(255,255,255,0.2);
        }
        h1 {
            text-align: center;
            font-size: 2.2rem;
            margin-bottom: 1.5rem;
            background: linear-gradient(45deg, #fff, #f0f0f0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .status-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            background: rgba(0,0,0,0.2);
            border-radius: 16px;
            margin-bottom: 2rem;
            font-size: 0.95rem;
        }
        .live-dot {
            display: inline-block;
            width: 12px;
            height: 12px;
            background: #10b981;
            border-radius: 50%;
            animation: pulse 1.5s infinite;
            margin-right: 0.5rem;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(1.1); }
        }
        .stats {
            display: grid;
            gap: 1.2rem;
        }
        .stat {
            display: flex;
            justify-content: space-between;
            padding: 1rem;
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            transition: all 0.3s ease;
        }
        .stat:hover {
            background: rgba(255,255,255,0.15);
            transform: translateX(8px);
        }
        .stat-label { opacity: 0.9; font-size: 0.95rem; }
        .stat-value { 
            font-weight: 700; 
            font-size: 1.3rem;
            min-width: 120px;
            text-align: right;
        }
        .db-ok { color: #10b981; }
        .db-error { color: #ef4444; }
        .footer {
            text-align: center;
            margin-top: 2rem;
            padding-top: 1.5rem;
            border-top: 1px solid rgba(255,255,255,0.2);
            font-size: 0.85rem;
            opacity: 0.8;
        }
        @media (max-width: 480px) {
            .card { padding: 2rem 1.5rem; }
            h1 { font-size: 1.8rem; }
            .stat { padding: 0.8rem; }
            .stat-value { font-size: 1.1rem; }
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>🔥 LIVE DASHBOARD</h1>
        
        <div class="status-bar">
            <span><span class="live-dot"></span>Live Update</span>
            <span id="last-update">-</span>
        </div>

        <div class="stats" id="stats">
            <!-- Stats populated by JS -->
        </div>

        <div class="footer">
            Auto-refreshing every 5s • Requests: <span id="request-count">0</span>
        </div>
    </div>

    <script>
        let requestCount = 0;
        
        function updateStats() {
            fetch('/api/live')
                .then(r => r.json())
                .then(data => {
                    requestCount++;
                    document.getElementById('request-count').textContent = requestCount;
                    document.getElementById('last-update').textContent = 
                        new Date(data.timestamp).toLocaleTimeString();
                    
                    const stats = document.getElementById('stats');
                    stats.innerHTML = `
                        <div class="stat">
                            <span class="stat-label">Pod Name</span>
                            <span class="stat-value">${data.pod_name}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Version</span>
                            <span class="stat-value">${data.version}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Git Hash</span>
                            <span class="stat-value">${data.git_hash}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Database</span>
                            <span class="stat-value ${data.db_status.includes('OK') ? 'db-ok' : 'db-error'}">${data.db_status}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Uptime</span>
                            <span class="stat-value">${data.uptime}s</span>
                        </div>
                    `;
                })
                .catch(e => console.error('Update failed:', e));
        }

        // Auto-update every 3 seconds
        setInterval(updateStats, 3000);
        updateStats(); // Initial load
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return HTML

@app.route('/api/live')
def api_live():
    live_data["requests"] += 1
    return jsonify(live_data)

@app.route('/health')
def health():
    return jsonify({"status": "ok", "db": live_data["db_status"]})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"🌟 Live Dashboard v{VERSION} starting on :{port}")
    print(f"🐳 Pod: {POD_NAME} | 💾 Git: {GIT_HASH}")
    app.run(host="0.0.0.0", port=port, debug=False)
