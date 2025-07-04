#!/bin/bash
# quick_fix.sh - Apply all fixes for Railway deployment

echo "🚀 Applying Railway deployment fixes..."

# Backup existing files
echo "📦 Creating backups..."
[ -f "src/main.py" ] && cp src/main.py src/main.py.backup
[ -f "src/utils/redis_client.py" ] && cp src/utils/redis_client.py src/utils/redis_client.py.backup
[ -f "src/utils/rate_limiting.py" ] && cp src/utils/rate_limiting.py src/utils/rate_limiting.py.backup

# Create directories if needed
mkdir -p src/utils

# Fix main.py (creating a minimal working version)
echo "📝 Fixing main.py..."
cat > src/main.py << 'MAINPY'
import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from sqlalchemy.exc import IntegrityError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize Redis
redis_client = None
redis_url = os.environ.get('REDIS_URL')
if redis_url:
    try:
        import redis
        redis_client = redis.from_url(redis_url)
        redis_client.ping()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.warning(f"⚠️ Redis failed: {e}")

# Initialize Database
try:
    from src.models import db, Admin
    db.init_app(app)
    with app.app_context():
        db.create_all()
        if not Admin.query.filter_by(username='admin').first():
            from werkzeug.security import generate_password_hash
            admin = Admin(
                username='admin',
                email='admin@biped.app',
                password_hash=generate_password_hash('admin123'),
                first_name='Admin',
                last_name='User',
                role='super_admin',
                is_active=True,
                is_super_admin=True
            )
            db.session.add(admin)
            db.session.commit()
except Exception as e:
    logger.error(f"DB Error: {e}")

# Routes
@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'redis': bool(redis_client)})

@app.route('/')
def index():
    return jsonify({'message': 'Biped Platform Running'})

# Register blueprints
try:
    from src.routes.auth import auth_bp
    from src.routes.admin import admin_bp
    from src.routes.api import api_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
except ImportError as e:
    logger.warning(f"Blueprint import error: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
MAINPY

# Fix rate_limiting.py
echo "📝 Fixing rate_limiting.py..."
cat > src/utils/rate_limiting.py << 'RATELIMIT'
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
RATELIMIT

# Fix redis_client.py
echo "📝 Fixing redis_client.py..."
cat > src/utils/redis_client.py << 'REDISCLIENT'
import os
import redis
import logging

logger = logging.getLogger(__name__)

def get_redis_client():
    redis_url = os.environ.get('REDIS_URL')
    if redis_url:
        try:
            client = redis.from_url(redis_url)
            client.ping()
            return client
        except Exception as e:
            logger.error(f"Redis error: {e}")
    return None
REDISCLIENT

# Update Procfile
echo "📝 Creating Procfile..."
echo "web: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:\$PORT src.main:app" > Procfile

# Ensure __init__.py files exist
touch src/__init__.py
touch src/utils/__init__.py

echo "
✅ All fixes applied!

Next steps:
1. Review the changes
2. Test locally: python src/main.py
3. Commit and push:
   git add .
   git commit -m 'Fix Railway deployment issues'
   git push

4. Check Railway logs after deployment
"