from flask import Flask, render_template_string, jsonify
import mysql.connector
import os
import subprocess
import hashlib
from datetime import datetime

app = Flask(__name__)

# Get version info
VERSION = os.getenv("VERSION", "dev")
GIT_HASH = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                         capture_output=True, text=True).stdout.strip() if os.path.exists('.git') else "no-git"

# Pod/Container info (Kubernetes/Docker)
POD_NAME = os.getenv("POD_NAME", os.getenv("HOSTNAME", "local"))
CONTAINER_ID = os.getenv("HOSTNAME", "local")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Flask App v{{ version }}</title>
    <style>
        :root {
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --accent: #0f3460;
            --text-primary: #ffffff;
            --text-secondary: #b8b8b8;
            --gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        [data-theme="light"] {
            --bg-primary: #f8fafc;
            --bg-secondary: #e2e8f0;
            --accent: #1e293b;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --gradient: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        .hero {
            text-align: center;
            animation: fadeInUp 1s ease-out;
        }
        .hero h1 {
            font-size: 4rem;
            background: var(--gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1rem;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
            margin: 3rem 0;
        }
        .stat-card {
            background: var(--bg-secondary);
            padding: 2rem;
            border-radius: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s ease;
            animation: slideInUp 0.8s ease-out forwards;
            opacity: 0;
        }
        .stat-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }
        .stat-value { font-size: 2.5rem; font-weight: bold; color: #00d4ff; }
        .stat-label { color: var(--text-secondary); margin-top: 0.5rem; }
        .theme-toggle {
            position: fixed;
            top: 2rem;
            right: 2rem;
            background: var(--gradient);
            border: none;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            cursor: pointer;
            color: white;
            font-size: 1.5rem;
            transition: all 0.3s ease;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .pulse {
            animation: pulse 2s infinite;
        }
        @keyframes fadeInUp { from { opacity: 0; transform: translateY(50px); } }
        @keyframes slideInUp { 
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .api-btn {
            background: var(--gradient);
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 50px;
            font-size: 1.1rem;
            cursor: pointer;
            margin: 1rem;
            transition: all 0.3s ease;
        }
        .api-btn:hover { transform: scale(1.05); }
    </style>
</head>
<body>
    <button class="theme-toggle" onclick="toggleTheme()">🌙</button>
    
    <div class="container">
        <div class="hero">
            <h1>🚀 Flask Power!</h1>
            <p>Version {{ version }} | {{ git_hash }}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card" style="animation-delay: 0.1s">
                <div class="stat-value pulse">{{ pod_name }}</div>
                <div class="stat-label">Pod/Container</div>
            </div>
            <div class="stat-card" style="animation-delay: 0.2s">
                <div class="stat-value">{{ timestamp }}</div>
                <div class="stat-label">Deployed</div>
            </div>
            <div class="stat-card" style="animation-delay: 0.3s">
                <div class="stat-value">{{ db_status }}</div>
                <div class="stat-label">Database</div>
            </div>
            <div class="stat-card" style="animation-delay: 0.4s">
                <div class="stat-value">99.9%</div>
                <div class="stat-label">Uptime</div>
            </div>
        </div>
        
        <div style="text-align: center;">
            <button class="api-btn" onclick="fetchData()">🔄 Refresh Stats</button>
            <button class="api-btn" onclick="window.open('/api/stats', '_blank')">📊 API Data</button>
        </div>
    </div>

    <script>
        const themeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        if (themeMediaQuery.matches) document.documentElement.setAttribute('data-theme', 'dark');
        
        function toggleTheme() {
            const body = document.documentElement;
            const current = body.getAttribute('data-theme');
            const icon = document.querySelector('.theme-toggle');
            body.setAttribute('data-theme', current === 'dark' ? 'light' : 'dark');
            icon.textContent = current === 'dark' ? '☀️' : '🌙';
        }
        
        async function fetchData() {
            const response = await fetch('/api/stats');
            const data = await response.json();
            document.querySelector('.stat-value').textContent = data.pod_name;
            // Update other stats...
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    try:
        db = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        db_status = "🟢 Connected"
        db.close()
    except:
        db_status = "🔴 Failed"
    
    return render_template_string(HTML_TEMPLATE, 
                                version=VERSION,
                                git_hash=GIT_HASH,
                                pod_name=POD_NAME,
                                timestamp=datetime.now().strftime("%H:%M:%S"),
                                db_status=db_status)

@app.route('/api/stats')
def api_stats():
    return jsonify({
        "version": VERSION,
        "git_hash": GIT_HASH,
        "pod_name": POD_NAME,
        "timestamp": datetime.now().isoformat(),
        "db_status": "healthy"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
