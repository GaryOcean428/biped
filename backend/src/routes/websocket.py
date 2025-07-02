"""
WebSocket Routes for Real-time Features
Handles real-time notifications, job updates, and live messaging
"""

from flask import Blueprint, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
import json
import logging
from datetime import datetime
from typing import Dict, Any

from ..utils.redis_client import redis_client, publish_notification
from ..models.user import User
from ..models.job import Job
from ..models.review import Message, Notification

logger = logging.getLogger(__name__)

# Create SocketIO instance (will be initialized in main app)
socketio = None

def init_socketio(app):
    """Initialize SocketIO with the Flask app"""
    global socketio
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        logger=True,
        engineio_logger=True
    )
    
    # Register event handlers
    register_socketio_events()
    
    return socketio

def register_socketio_events():
    """Register all WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect(auth):
        """Handle client connection"""
        try:
            # Get user from session or auth token
            user_id = session.get('user_id')
            if not user_id and auth:
                # Handle token-based auth if needed
                user_id = validate_auth_token(auth.get('token'))
            
            if user_id:
                # Join user-specific room
                join_room(f"user_{user_id}")
                
                # Store user session info in Redis
                redis_client.set_session(request.sid, {
                    'user_id': user_id,
                    'connected_at': datetime.utcnow().isoformat()
                })
                
                # Send welcome message
                emit('connected', {
                    'status': 'success',
                    'message': 'Connected to real-time updates',
                    'user_id': user_id
                })
                
                # Send any pending notifications
                send_pending_notifications(user_id)
                
                logger.info(f"User {user_id} connected via WebSocket")
            else:
                logger.warning("Unauthorized WebSocket connection attempt")
                disconnect()
                
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            emit('error', {'message': 'Connection failed'})
            disconnect()
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        try:
            # Get user session
            session_data = redis_client.get_session(request.sid)
            if session_data:
                user_id = session_data.get('user_id')
                if user_id:
                    leave_room(f"user_{user_id}")
                    logger.info(f"User {user_id} disconnected from WebSocket")
                
                # Clean up session
                redis_client.delete_session(request.sid)
                
        except Exception as e:
            logger.error(f"WebSocket disconnection error: {e}")
    
    @socketio.on('join_job_room')
    def handle_join_job_room(data):
        """Join a job-specific room for updates"""
        try:
            job_id = data.get('job_id')
            user_id = get_current_user_id()
            
            if not job_id or not user_id:
                emit('error', {'message': 'Invalid job ID or user'})
                return
            
            # Verify user has access to this job
            if verify_job_access(user_id, job_id):
                join_room(f"job_{job_id}")
                emit('joined_job_room', {'job_id': job_id})
                logger.info(f"User {user_id} joined job room {job_id}")
            else:
                emit('error', {'message': 'Access denied to job'})
                
        except Exception as e:
            logger.error(f"Join job room error: {e}")
            emit('error', {'message': 'Failed to join job room'})
    
    @socketio.on('leave_job_room')
    def handle_leave_job_room(data):
        """Leave a job-specific room"""
        try:
            job_id = data.get('job_id')
            user_id = get_current_user_id()
            
            if job_id and user_id:
                leave_room(f"job_{job_id}")
                emit('left_job_room', {'job_id': job_id})
                logger.info(f"User {user_id} left job room {job_id}")
                
        except Exception as e:
            logger.error(f"Leave job room error: {e}")
    
    @socketio.on('send_message')
    def handle_send_message(data):
        """Handle real-time messaging"""
        try:
            user_id = get_current_user_id()
            if not user_id:
                emit('error', {'message': 'User not authenticated'})
                return
            
            job_id = data.get('job_id')
            message_text = data.get('message', '').strip()
            
            if not job_id or not message_text:
                emit('error', {'message': 'Invalid message data'})
                return
            
            # Verify user has access to this job
            if not verify_job_access(user_id, job_id):
                emit('error', {'message': 'Access denied'})
                return
            
            # Create message in database
            message = Message(
                job_id=job_id,
                sender_id=user_id,
                content=message_text,
                timestamp=datetime.utcnow()
            )
            
            # Save to database (you'll need to implement this)
            # db.session.add(message)
            # db.session.commit()
            
            # Broadcast to job room
            message_data = {
                'id': message.id if hasattr(message, 'id') else None,
                'job_id': job_id,
                'sender_id': user_id,
                'sender_name': get_user_name(user_id),
                'content': message_text,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            socketio.emit('new_message', message_data, room=f"job_{job_id}")
            
            # Send push notification to other participants
            notify_job_participants(job_id, user_id, f"New message in job #{job_id}")
            
            logger.info(f"Message sent by user {user_id} in job {job_id}")
            
        except Exception as e:
            logger.error(f"Send message error: {e}")
            emit('error', {'message': 'Failed to send message'})
    
    @socketio.on('job_status_update')
    def handle_job_status_update(data):
        """Handle job status updates"""
        try:
            user_id = get_current_user_id()
            if not user_id:
                emit('error', {'message': 'User not authenticated'})
                return
            
            job_id = data.get('job_id')
            new_status = data.get('status')
            
            if not job_id or not new_status:
                emit('error', {'message': 'Invalid update data'})
                return
            
            # Verify user can update this job
            if not verify_job_update_access(user_id, job_id):
                emit('error', {'message': 'Access denied'})
                return
            
            # Update job status (implement database update)
            # job = Job.query.get(job_id)
            # if job:
            #     job.status = new_status
            #     db.session.commit()
            
            # Broadcast update to job room
            update_data = {
                'job_id': job_id,
                'status': new_status,
                'updated_by': user_id,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            socketio.emit('job_status_changed', update_data, room=f"job_{job_id}")
            
            # Notify participants
            notify_job_participants(job_id, user_id, f"Job #{job_id} status updated to {new_status}")
            
            logger.info(f"Job {job_id} status updated to {new_status} by user {user_id}")
            
        except Exception as e:
            logger.error(f"Job status update error: {e}")
            emit('error', {'message': 'Failed to update job status'})
    
    @socketio.on('typing_start')
    def handle_typing_start(data):
        """Handle typing indicator start"""
        try:
            user_id = get_current_user_id()
            job_id = data.get('job_id')
            
            if user_id and job_id and verify_job_access(user_id, job_id):
                socketio.emit('user_typing', {
                    'user_id': user_id,
                    'user_name': get_user_name(user_id),
                    'job_id': job_id
                }, room=f"job_{job_id}", include_self=False)
                
        except Exception as e:
            logger.error(f"Typing start error: {e}")
    
    @socketio.on('typing_stop')
    def handle_typing_stop(data):
        """Handle typing indicator stop"""
        try:
            user_id = get_current_user_id()
            job_id = data.get('job_id')
            
            if user_id and job_id and verify_job_access(user_id, job_id):
                socketio.emit('user_stopped_typing', {
                    'user_id': user_id,
                    'job_id': job_id
                }, room=f"job_{job_id}", include_self=False)
                
        except Exception as e:
            logger.error(f"Typing stop error: {e}")

def get_current_user_id():
    """Get current user ID from session"""
    session_data = redis_client.get_session(request.sid)
    return session_data.get('user_id') if session_data else None

def get_user_name(user_id):
    """Get user name by ID"""
    # Implement user lookup
    # user = User.query.get(user_id)
    # return f"{user.first_name} {user.last_name}" if user else "Unknown User"
    return f"User {user_id}"  # Placeholder

def verify_job_access(user_id, job_id):
    """Verify user has access to job"""
    # Implement job access verification
    # job = Job.query.get(job_id)
    # return job and (job.customer_id == user_id or job.provider_id == user_id)
    return True  # Placeholder

def verify_job_update_access(user_id, job_id):
    """Verify user can update job status"""
    # Implement job update access verification
    # job = Job.query.get(job_id)
    # return job and job.provider_id == user_id
    return True  # Placeholder

def validate_auth_token(token):
    """Validate authentication token"""
    # Implement token validation
    # return decode_jwt_token(token)
    return None  # Placeholder

def send_pending_notifications(user_id):
    """Send any pending notifications to user"""
    try:
        # Get pending notifications from Redis or database
        notifications = get_pending_notifications(user_id)
        
        for notification in notifications:
            socketio.emit('notification', notification, room=f"user_{user_id}")
            
    except Exception as e:
        logger.error(f"Send pending notifications error: {e}")

def get_pending_notifications(user_id):
    """Get pending notifications for user"""
    # Implement notification retrieval
    return []  # Placeholder

def notify_job_participants(job_id, sender_id, message):
    """Send notification to all job participants except sender"""
    try:
        # Get job participants
        participants = get_job_participants(job_id)
        
        for participant_id in participants:
            if participant_id != sender_id:
                # Send real-time notification
                socketio.emit('notification', {
                    'type': 'job_update',
                    'message': message,
                    'job_id': job_id,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=f"user_{participant_id}")
                
                # Store notification in Redis for offline users
                redis_client.publish_notification(f"user_{participant_id}", {
                    'type': 'job_update',
                    'message': message,
                    'job_id': job_id
                })
                
    except Exception as e:
        logger.error(f"Notify job participants error: {e}")

def get_job_participants(job_id):
    """Get all participants in a job"""
    # Implement participant retrieval
    # job = Job.query.get(job_id)
    # return [job.customer_id, job.provider_id] if job else []
    return []  # Placeholder

# Utility functions for sending notifications
def send_user_notification(user_id, notification_type, message, data=None):
    """Send notification to specific user"""
    try:
        notification_data = {
            'type': notification_type,
            'message': message,
            'data': data or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Send real-time notification if user is connected
        socketio.emit('notification', notification_data, room=f"user_{user_id}")
        
        # Store in Redis for offline users
        redis_client.publish_notification(f"user_{user_id}", notification_data)
        
        logger.info(f"Notification sent to user {user_id}: {message}")
        
    except Exception as e:
        logger.error(f"Send user notification error: {e}")

def broadcast_system_notification(message, notification_type='info'):
    """Broadcast notification to all connected users"""
    try:
        notification_data = {
            'type': 'system',
            'level': notification_type,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        socketio.emit('notification', notification_data, broadcast=True)
        
        logger.info(f"System notification broadcasted: {message}")
        
    except Exception as e:
        logger.error(f"Broadcast system notification error: {e}")

def send_job_update(job_id, update_type, data):
    """Send job update to all participants"""
    try:
        update_data = {
            'type': update_type,
            'job_id': job_id,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        socketio.emit('job_update', update_data, room=f"job_{job_id}")
        
        logger.info(f"Job update sent for job {job_id}: {update_type}")
        
    except Exception as e:
        logger.error(f"Send job update error: {e}")

# Create blueprint for HTTP endpoints related to WebSocket
websocket_bp = Blueprint('websocket', __name__)

@websocket_bp.route('/ws/health')
def websocket_health():
    """WebSocket health check endpoint"""
    return {
        'status': 'healthy',
        'websocket_enabled': socketio is not None,
        'redis_connected': redis_client.is_connected()
    }

@websocket_bp.route('/ws/stats')
def websocket_stats():
    """WebSocket statistics endpoint"""
    try:
        # Get connected users count from Redis
        connected_users = len(redis_client.redis_client.keys("session:*")) if redis_client.is_connected() else 0
        
        return {
            'connected_users': connected_users,
            'redis_connected': redis_client.is_connected(),
            'socketio_initialized': socketio is not None
        }
    except Exception as e:
        logger.error(f"WebSocket stats error: {e}")
        return {'error': str(e)}, 500

