#!/usr/bin/env python3
"""Simple Flask server to test the UI functionality"""

import os
import json
from datetime import datetime
from flask import Flask, send_from_directory, jsonify, render_template_string, request

app = Flask(__name__, static_folder='backend/src/static')

# Simple in-memory storage for demo purposes
jobs = []

@app.route('/')
def index():
    return send_from_directory('backend/src/static', 'index.html')

@app.route('/index.html')
def index_html():
    return send_from_directory('backend/src/static', 'index.html')

@app.route('/jobs')
def jobs_page():
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

@app.route('/api/jobs', methods=['POST'])
def submit_job():
    """Handle job submission from the job posting form"""
    try:
        data = request.get_json()
        
        # Create a new job entry
        job = {
            'id': f'PRJ-{len(jobs) + 1248}',
            'title': data.get('title', 'Untitled Project'),
            'description': data.get('description', ''),
            'category': data.get('category', ''),
            'budget': data.get('budget', ''),
            'timeline': data.get('timeline', ''),
            'location': data.get('location', ''),
            'status': 'Pending',
            'created_at': datetime.now().isoformat(),
            'customer': 'Anonymous User'  # In real app, this would come from auth
        }
        
        jobs.append(job)
        
        return jsonify({
            'success': True,
            'message': 'Job posted successfully!',
            'job_id': job['id'],
            'estimated_providers': 5
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error submitting job: {str(e)}'
        }), 400

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get all jobs for dashboard"""
    return jsonify({
        'success': True,
        'jobs': jobs,
        'total': len(jobs)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)