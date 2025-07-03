#!/usr/bin/env python3
"""Simple Flask server to test the UI functionality"""

import os
from flask import Flask, send_from_directory, jsonify, render_template_string

app = Flask(__name__, static_folder='backend/src/static')

@app.route('/')
def index():
    return send_from_directory('backend/src/static', 'index-enhanced.html')

@app.route('/jobs')
def jobs():
    return send_from_directory('backend/src/static', 'enhanced-job-posting.html')

@app.route('/dashboard')
def dashboard():
    return send_from_directory('backend/src/static', 'dashboard.html')

@app.route('/provider-dashboard')
def provider_dashboard():
    return send_from_directory('backend/src/static', 'provider-dashboard.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('backend/src/static', filename)

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'message': 'Biped Platform Running'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)