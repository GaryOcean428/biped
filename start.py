#!/usr/bin/env python3
"""
Simple startup script for Railway deployment
Ensures proper working directory and imports
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main startup function"""
    
    # Get the current directory
    current_dir = os.getcwd()
    logger.info(f"Current directory: {current_dir}")
    
    # Add backend to Python path
    backend_dir = os.path.join(current_dir, 'backend')
    if os.path.exists(backend_dir):
        sys.path.insert(0, backend_dir)
        os.chdir(backend_dir)
        logger.info(f"Changed to backend directory: {backend_dir}")
    else:
        logger.info("Backend directory not found, assuming we're already in it")
    
    # Set environment variables
    os.environ.setdefault('PYTHONPATH', os.getcwd())
    
    # Import and run the app
    try:
        from src.main import app
        port = int(os.environ.get('PORT', 8080))
        logger.info(f"Starting Flask app on port {port}")
        
        # Use Gunicorn programmatically
        from gunicorn.app.wsgiapp import WSGIApplication
        
        class StandaloneApplication(WSGIApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()
            
            def load_config(self):
                for key, value in self.options.items():
                    self.cfg.set(key.lower(), value)
            
            def load(self):
                return self.application
        
        options = {
            'bind': f'0.0.0.0:{port}',
            'workers': 1,
            'timeout': 120,
            'accesslog': '-',
            'errorlog': '-',
            'loglevel': 'info'
        }
        
        StandaloneApplication(app, options).run()
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

