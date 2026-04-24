from flask import Flask, render_template_string, jsonify, Response
import mysql.connector
import os
import subprocess
import hashlib
from datetime import datetime
import json
import time

app = Flask(__name__, static_folder='static')

# Version info
VERSION = os.getenv("VERSION", "dev")
GIT_HASH = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                         capture_output=True, text=True).stdout.strip() if os.path.exists('.git') else "no-git"
POD_NAME = os.getenv("HOSTNAME", os.getenv("POD_NAME", "local"))

CSS_TEMPLATE = """
:root {
    --bg-primary: #0f0f23;
    --bg-secondary: #1a1a2e;
    --bg-card: #242440;
    --accent-primary: #00d4ff;
    --accent-secondary: #7c3aed;
    --text-primary: #ffffff;
    --text-secondary: #a0a0c0;
    --border: rgba(255,255,255,0.1);
    --shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
    --gradient: linear-gradient(135deg, #00d4ff 0%, #7c3aed 50%, #ff6b6b 100%);
    --success: #10b981;
}

[data-theme="light"] {
    --bg-primary: #f8fafc;
    --bg-secondary: #f1f5f9;
    --bg-card: #ffffff;
    --accent-primary: #0ea5e9;
    --accent-secondary: #8b5cf6;
    --text-primary: #0f172a;
    --text-secondary: #64748b;
    --border: rgba(0,0,0,0.08);
    --shadow: 0 20px 25px -5px rgba(0,0,0,0.1);
    --gradient: linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 50%, #f59e0b 100%);
    --success: #059669;
}

/* ... [keeping all your existing CSS] ... */

.auto-update-banner {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    background: linear-gradient(90deg, var(--success), #f59e0b);
    color: white;
    padding: 1rem 2rem;
    text-align: center;
    font-weight: 800;
    font-size: 1.3rem;
    z-index: 10000;
    animation: glow 2s ease-in-out infinite alternate;
    box-shadow: 0 4px 20px rgba(16,185,129,0.4);
}

@keyframes glow {
    0% { box-shadow: 0 4px 20px rgba(16,185,129,0.4); }
    100% { box-shadow: 0 4px 30px rgba(16,185,129,0.6); }
}

.live-indicator {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(16,185,129,0.2);
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 600;
}

.live-dot {
    width: 10px;
    height: 10px;
    background: var(--success);
    border-radius: 50%;
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.2); }
}
"""

JS_TEMPLATE = """
<script>
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');

function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-theme') === 'dark';
    html.setAttribute('data-theme', isDark ? 'light' : 'dark');
    localStorage.setItem('theme', isDark ? 'light' : 'dark');
}

document.querySelector('.theme-toggle').addEventListener('click', toggleTheme);

const savedTheme = localStorage.getItem('theme');
if (savedTheme) {
    document.documentElement.setAttribute('data-theme', savedTheme);
}

let isRefreshing = false;
let lastUpdate = 0;
const AUTO_REFRESH_INTERVAL = 10000; // 10 seconds

async function refreshStats() {
    if (isRefreshing) return;

    isRefreshing = true;
    const now = Date.now();
    
    // Only refresh if 10s passed
    if (now - lastUpdate < AUTO_REFRESH_INTERVAL) {
        isRefreshing = false;
        return;
    }

    const btn = document.querySelector('#refresh-btn');
    const liveIndicator = document.querySelector('.live-indicator');
    
    btn.disabled = true;
    btn.innerHTML = '⏳ Updating...';
    liveIndicator.innerHTML = '<span class="live-dot"></span>Updating...';

    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        // Update all stats
        document.querySelector('[data-stat="pod"]').textContent = data.pod_name;
        document.querySelector('[data-stat="version"]').textContent = data.version;
        document.querySelector('[data-stat="git"]').textContent = data.git_hash;
        document.querySelector('[data-stat="timestamp"]').textContent = new Date(data.timestamp).toLocaleString();
        document.querySelector('[data-stat="db"]').textContent = data.db_status === 'healthy' ? '🟢 Healthy' : '🔴 Error';

        // Update live indicator
        liveIndicator.innerHTML = `<span class="live-dot"></span>Live • ${new Date().toLocaleTimeString()}`;
        
        lastUpdate = now;
        console.log('✅ Auto-update successful:', data);

    } catch (error) {
        console.error('❌ Auto-update failed:', error);
        document.querySelector('.live-indicator').innerHTML = '<span class="live-dot" style="background:red;"></span>Error';
    } finally {
        isRefreshing = false;
        btn.disabled = false;
        btn.innerHTML = '🔄 Live Update';
    }
}

async function showApiData() {
    const response = await fetch('/api/stats');
    const data = await response.json();

    document.getElementById('json-data').textContent = JSON.stringify(data, null, 2);
    document.getElementById('modal').style.display = 'block';
}

function closeModal() {
    document.getElementById('modal').style.display = 'none';
}

// 🔥 SUPERCHARGED AUTO-UPDATE: Every 10 seconds!
setInterval(refreshStats, AUTO_REFRESH_INTERVAL);

// Initial load + manual refresh
refreshStats();

// Visual heartbeat every 2 seconds
setInterval(() => {
    const liveDot = document.querySelector('.live-dot');
    if (liveDot && !isRefreshing) {
        liveDot.style.animationPlayState = 'running';
    }
}, 2000);

console.log('🚀 Dashboard loaded - Auto-update active!');
</script>
"""

@app.route('/')
def home():
    try:
        db = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "test")
        )
        db_status = "🟢 Healthy"
        db.close()
    except Exception as e:
        db_status = "🔴 Error"

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Flask Dashboard v{VERSION} - LIVE</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🔥</text></svg>">
    <style>{CSS_TEMPLATE}</style>
</head>
<body>
    <!-- 🔥 AUTO UPDATE BANNER 🔥 -->
    <div class="auto-update-banner">
        <h1>🔥 AUTO UPDATE WORKING 🔥</h1>
        <div class="live-indicator">
            <span class="live-dot"></span>Live
        </div>
    </div>

    <button class="theme-toggle" title="Toggle Theme" aria-label="Toggle dark/light mode">🌙</button>

    <div class="container">
        <div class="hero">
            <h1>🚀 Flask Dashboard</h1>
            <p class="hero-subtitle">Production-ready, mobile-first, <strong>LIVE auto-updating</strong> monitoring</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card" style="animation: slideInUp 0.6s ease-out;">
                <div class="stat-value" data-stat="pod">{POD_NAME}</div>
                <div class="stat-label">Pod/Container</div>
            </div>
            <div class="stat-card" style="animation: slideInUp 0.8s ease-out;">
                <div class="stat-value" data-stat="version">{VERSION}</div>
                <div class="stat-label">Version</div>
            </div>
            <div class="stat-card" style="animation: slideInUp 1s ease-out;">
                <div class="stat-value" data-stat="git">{GIT_HASH}</div>
                <div class="stat-label">Git Hash</div>
            </div>
            <div class="stat-card" style="animation: slideInUp 1.2s ease-out;">
                <div class="stat-value" data-stat="db">{db_status}</div>
                <div class="stat-label">Database</div>
            </div>
            <div class="stat-card" style="animation: slideInUp 1.4s ease-out;">
                <div class="stat-value" data-stat="timestamp">{datetime.now().strftime('%H:%M:%S')}</div>
                <div class="stat-label">Last Update</div>
            </div>
        </div>

        <div class="controls">
            <button id="refresh-btn" class="btn" onclick="refreshStats()">🔄 Force Live Update</button>
            <a href="#" class="btn" onclick="showApiData(); return false;">📊 Raw API Data</a>
        </div>
    </div>

    <div id="modal" class="modal" onclick="closeModal()">
        <div class="modal-content" onclick="event.stopPropagation()">
            <h3 style="margin-bottom: 1rem;">📊 Live API Response</h3>
            <pre id="json-data" class="json-pre"></pre>
            <button class="btn" onclick="closeModal()" style="margin-top: 1rem;">Close</button>
        </div>
    </div>

    {JS_TEMPLATE}
</body>
</html>
    """
    return html

# ... [keep all your existing routes unchanged] ...

@app.route('/api/stats')
def api_stats():
    try:
        db = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "test"),
            connection_timeout=5
        )
        db_status = "healthy"
        db.close()
    except:
        db_status = "error"

    return jsonify({
        "version": VERSION,
        "git_hash": GIT_HASH,
        "pod_name": os.getenv("HOSTNAME", POD_NAME),
        "timestamp": datetime.now().isoformat(),
        "db_status": db_status,
        "uptime": time.time()  # For demo purposes
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "version": VERSION})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 Starting Flask Dashboard v{VERSION} on port {port}")
    print(f"📦 Git: {GIT_HASH} | 🖥️  Pod: {POD_NAME}")
    app.run(host="0.0.0.0", port=port, debug=False)
