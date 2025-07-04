#!/usr/bin/env python3
"""
Simplified test server to diagnose the /post-job 502 error
"""

import os
import sys
import logging
from flask import Flask, jsonify, request

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
    """Test root endpoint"""
    return jsonify({
        'message': 'Biped Test Server Running',
        'status': 'healthy'
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'server': 'test'
    })

@app.route('/post-job', methods=['GET'])
def post_job_page():
    """Test the /post-job endpoint"""
    try:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Post a Job - Biped</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <h1>Post a Job - Test</h1>
            <p>This is a simplified test version of the job posting page.</p>
            <form>
                <label>Job Title:</label><br>
                <input type="text" name="title" required><br><br>
                <label>Description:</label><br>
                <textarea name="description" required></textarea><br><br>
                <button type="submit">Submit</button>
            </form>
            <a href="/">← Back to Home</a>
        </body>
        </html>
        '''
    except Exception as e:
        logger.error(f"Error loading post job page: {e}")
        return f"<h1>Error</h1><p>Unable to load job posting page: {str(e)}</p>", 500

@app.route('/api/jobs', methods=['POST'])
def create_job():
    """Test job creation endpoint"""
    try:
        data = request.get_json() if request.is_json else {}
        logger.info(f"Received job creation request: {data}")
        
        return jsonify({
            'success': True,
            'job_id': 123,
            'message': 'Job posted successfully (test)!'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        return jsonify({'error': f'Failed to create job: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting test server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)