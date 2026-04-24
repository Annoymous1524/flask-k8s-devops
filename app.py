from flask import Flask, render_template_string, jsonify, Response
import mysql.connector
import os
import subprocess
import hashlib
from datetime import datetime
import json

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
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    min-height: 100vh;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1.5rem;
}

.hero {
    text-align: center;
    padding: 2rem 0;
    animation: fadeIn 1s ease-out;
}

.hero h1 {
    font-size: clamp(2.5rem, 8vw, 4.5rem);
    font-weight: 800;
    background: var(--gradient);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 1rem;
    line-height: 1.1;
}

.hero-subtitle {
    font-size: clamp(1rem, 3vw, 1.25rem);
    color: var(--text-secondary);
    max-width: 600px;
    margin: 0 auto;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
    margin: 3rem 0;
}

.stat-card {
    background: var(--bg-card);
    padding: 2rem;
    border-radius: 24px;
    border: 1px solid var(--border);
    backdrop-filter: blur(20px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.stat-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: var(--gradient);
}

.stat-card:hover {
    transform: translateY(-8px);
    box-shadow: var(--shadow);
}

.stat-value {
    font-size: clamp(2rem, 6vw, 3.5rem);
    font-weight: 800;
    color: var(--accent-primary);
    margin-bottom: 0.5rem;
}

.stat-label {
    color: var(--text-secondary);
    font-size: 1.1rem;
    font-weight: 500;
}

.controls {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    justify-content: center;
    margin: 2rem 0;
}

.btn {
    background: var(--gradient);
    color: white;
    border: none;
    padding: 1rem 2rem;
    border-radius: 50px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    min-height: 52px;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    text-decoration: none;
    box-shadow: 0 10px 20px rgba(0,0,0,0.2);
}

.btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 15px 30px rgba(0,0,0,0.3);
}

.btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
}

.theme-toggle {
    position: fixed;
    top: 1.5rem;
    right: 1.5rem;
    z-index: 1000;
    width: 56px;
    height: 56px;
    border-radius: 50%;
    border: none;
    background: var(--bg-card);
    color: var(--text-primary);
    font-size: 1.25rem;
    cursor: pointer;
    box-shadow: var(--shadow);
    transition: all 0.3s ease;
}

.theme-toggle:hover {
    transform: scale(1.1);
}

.loading {
    opacity: 0.7;
    pointer-events: none;
}

.modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.8);
    z-index: 2000;
    backdrop-filter: blur(10px);
}

.modal-content {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: var(--bg-card);
    padding: 2rem;
    border-radius: 24px;
    max-width: 90vw;
    max-height: 90vh;
    overflow-y: auto;
    border: 1px solid var(--border);
}

.json-pre {
    background: var(--bg-secondary);
    padding: 1.5rem;
    border-radius: 16px;
    font-family: 'Monaco', monospace;
    font-size: 0.9rem;
    line-height: 1.6;
    white-space: pre-wrap;
    color: var(--accent-primary);
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes slideInUp {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
    .container { padding: 1rem; }
    .stats-grid { grid-template-columns: 1fr; gap: 1rem; }
    .controls { flex-direction: column; align-items: center; }
    .btn { width: 100%; max-width: 300px; justify-content: center; }
}

@media (prefers-reduced-motion: reduce) {
    * { animation-duration: 0.01ms !important; }
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

// Load saved theme
const savedTheme = localStorage.getItem('theme');
if (savedTheme) {
    document.documentElement.setAttribute('data-theme', savedTheme);
}

let isRefreshing = false;

async function refreshStats() {
    if (isRefreshing) return;
    
    isRefreshing = true;
    const btn = document.querySelector('#refresh-btn');
    btn.disabled = true;
    btn.innerHTML = '⏳ Loading...';
    btn.classList.add('loading');
    
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        // Update DOM
        document.querySelector('[data-stat="pod"]').textContent = data.pod_name;
        document.querySelector('[data-stat="version"]').textContent = data.version;
        document.querySelector('[data-stat="git"]').textContent = data.git_hash;
        document.querySelector('[data-stat="timestamp"]').textContent = new Date(data.timestamp).toLocaleString();
        document.querySelector('[data-stat="db"]').textContent = data.db_status === 'healthy' ? '🟢 Healthy' : '🔴 Error';
        
    } catch (error) {
        console.error('Refresh failed:', error);
    } finally {
        isRefreshing = false;
        btn.disabled = false;
        btn.innerHTML = '🔄 Refresh Stats';
        btn.classList.remove('loading');
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

// Auto refresh every 30s
setInterval(refreshStats, 30000);

// Initial load
refreshStats();
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
    <title>🚀 Flask Dashboard v{VERSION}</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🚀</text></svg>">
    <style>{CSS_TEMPLATE}</style>
</head>
<body>
    <button class="theme-toggle" title="Toggle Theme" aria-label="Toggle dark/light mode">🌙</button>
    
    <div class="container">
        <div class="hero">
            <h1>🚀 Flask Dashboard</h1>
            <p class="hero-subtitle">Production-ready, mobile-first, real-time monitoring</p>
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
            <button id="refresh-btn" class="btn" onclick="refreshStats()">🔄 Refresh Stats</button>
            <a href="#" class="btn" onclick="showApiData(); return false;">📊 View API Data</a>
        </div>
    </div>
    
    <div id="modal" class="modal" onclick="closeModal()">
        <div class="modal-content" onclick="event.stopPropagation()">
            <h3 style="margin-bottom: 1rem;">📊 Raw API Response</h3>
            <pre id="json-data" class="json-pre"></pre>
            <button class="btn" onclick="closeModal()" style="margin-top: 1rem;">Close</button>
        </div>
    </div>
    
    {JS_TEMPLATE}
</body>
</html>
    """
    return html

@app.route('/api/stats')
def api_stats():
    try:
        db = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "test")
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
        "db_status": db_status
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "version": VERSION})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
