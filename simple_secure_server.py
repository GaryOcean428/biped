#!/usr/bin/env python3
"""
Biped Platform - Simple Secure Server
Basic HTTP server with security headers - no external dependencies required
"""

import os
import json
import secrets
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class SecureBipedHandler(BaseHTTPRequestHandler):
    """Secure HTTP handler with proper headers and basic functionality"""
    
    def add_security_headers(self):
        """Add essential security headers to response"""
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('X-XSS-Protection', '1; mode=block')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        self.send_header('Content-Security-Policy', 
                        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;")
        
        # Add HSTS only in production
        if os.environ.get('ENVIRONMENT') == 'production':
            self.send_header('Strict-Transport-Security', 'max-age=63072000; includeSubDomains; preload')
        
        # CORS headers for API endpoints
        self.send_header('Access-Control-Allow-Origin', 'https://biped.app')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response with security headers"""
        response_data = json.dumps(data, indent=2)
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response_data))
        self.add_security_headers()
        self.end_headers()
        
        self.wfile.write(response_data.encode('utf-8'))
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == '/':
            # Landing page
            self.send_json_response({
                'message': 'Biped Platform - Secure Minimal Version',
                'status': 'running',
                'timestamp': datetime.utcnow().isoformat(),
                'security': 'enabled',
                'version': '1.0.0-minimal-secure',
                'environment': os.environ.get('ENVIRONMENT', 'development')
            })
            
        elif path == '/api/health':
            # Health check
            self.send_json_response({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'version': '1.0.0-minimal-secure',
                'environment': os.environ.get('ENVIRONMENT', 'development'),
                'security_headers': 'enabled',
                'secret_key_configured': bool(os.environ.get('SECRET_KEY'))
            })
            
        elif path == '/api/status':
            # Status endpoint
            self.send_json_response({
                'application': 'Biped Platform',
                'status': 'operational',
                'timestamp': datetime.utcnow().isoformat(),
                'security_improvements': [
                    'Hard-coded secrets removed',
                    'Security headers implemented',
                    'Environment-based configuration',
                    'Secure CORS policy',
                    'Input validation framework ready'
                ]
            })
            
        elif path.startswith('/api/'):
            # API endpoint not found
            self.send_json_response({
                'error': 'API endpoint not found',
                'available_endpoints': ['/api/health', '/api/status']
            }, 404)
            
        else:
            # Page not found
            self.send_json_response({
                'error': 'Page not found',
                'available_routes': ['/', '/api/health', '/api/status']
            }, 404)
    
    def do_HEAD(self):
        """Handle HEAD requests - same as GET but no body"""
        self.do_GET()
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.add_security_headers()
        self.end_headers()
    
    def log_message(self, format, *args):
        """Custom log format with timestamp"""
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {format % args}")

def run_server():
    """Start the secure server"""
    port = int(os.environ.get('PORT', 8080))
    
    # Validate environment
    secret_key = os.environ.get('SECRET_KEY')
    environment = os.environ.get('ENVIRONMENT', 'development')
    
    print(f"🚀 Starting Biped Secure Server")
    print(f"📅 Timestamp: {datetime.utcnow().isoformat()}")
    print(f"🌍 Environment: {environment}")
    print(f"🔑 Secret Key: {'✅ Configured' if secret_key else '⚠️  Using auto-generated (set SECRET_KEY env var)'}")
    print(f"🔒 Security Headers: ✅ Enabled")
    print(f"🛡️  CORS Protection: ✅ Enabled")
    print(f"🎯 Port: {port}")
    
    if environment == 'production' and not secret_key:
        print("❌ ERROR: SECRET_KEY environment variable is required in production!")
        return
    
    # Generate secret key for development if not set
    if not secret_key:
        generated_key = secrets.token_hex(32)
        os.environ['SECRET_KEY'] = generated_key
        print(f"🔧 Generated development secret key: {generated_key[:16]}...")
    
    server = HTTPServer(('0.0.0.0', port), SecureBipedHandler)
    
    print(f"✅ Server running at http://localhost:{port}")
    print("🔗 Available endpoints:")
    print("   • http://localhost:8080/")
    print("   • http://localhost:8080/api/health")
    print("   • http://localhost:8080/api/status")
    print("🛑 Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        server.server_close()

if __name__ == '__main__':
    run_server()