"""
Real-Time Notifications System for Biped Platform
Advanced notification management with WebSocket support
"""

import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from flask import Blueprint, g, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from sqlalchemy import and_, desc, or_
from src.models.job import Job, JobStatus
from src.models.user import User, db

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


class NotificationType(Enum):
    JOB_CREATED = "job_created"
    JOB_MATCHED = "job_matched"
    JOB_ACCEPTED = "job_accepted"
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    QUOTE_RECEIVED = "quote_received"
    QUOTE_ACCEPTED = "quote_accepted"
    PAYMENT_RECEIVED = "payment_received"
    REVIEW_RECEIVED = "review_received"
    MESSAGE_RECEIVED = "message_received"
    SYSTEM_ALERT = "system_alert"
    PROMOTION = "promotion"


class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Notification(db.Model):
    """Notification model for storing notifications"""

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    type = db.Column(db.Enum(NotificationType), nullable=False)
    priority = db.Column(db.Enum(NotificationPriority), default=NotificationPriority.MEDIUM)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    data = db.Column(db.JSON)  # Additional data for the notification
    is_read = db.Column(db.Boolean, default=False)
    is_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)

    # Relationships
    user = db.relationship("User", backref="user_notifications")


class NotificationManager:
    """Advanced notification management system"""

    def __init__(self, socketio=None):
        self.socketio = socketio
        self.active_connections = {}  # user_id -> socket_id mapping

    def create_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Optional[Dict] = None,
    ) -> Notification:
        """Create a new notification"""
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            priority=priority,
            title=title,
            message=message,
            data=data or {},
        )

        db.session.add(notification)
        db.session.commit()

        # Send real-time notification if user is connected
        self.send_real_time_notification(notification)

        return notification

    def send_real_time_notification(self, notification: Notification):
        """Send real-time notification via WebSocket"""
        if not self.socketio:
            return

        user_room = f"user_{notification.user_id}"
        notification_data = {
            "id": notification.id,
            "type": notification.type.value,
            "priority": notification.priority.value,
            "title": notification.title,
            "message": notification.message,
            "data": notification.data,
            "created_at": notification.created_at.isoformat(),
            "is_read": notification.is_read,
        }

        self.socketio.emit("new_notification", notification_data, room=user_room)
        notification.is_sent = True
        db.session.commit()

    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark notification as read"""
        notification = (
            db.session.query(Notification)
            .filter(and_(Notification.id == notification_id, Notification.user_id == user_id))
            .first()
        )

        if notification and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.session.commit()
            return True

        return False

    def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        count = (
            db.session.query(Notification)
            .filter(and_(Notification.user_id == user_id, Notification.is_read == False))
            .update({"is_read": True, "read_at": datetime.utcnow()})
        )

        db.session.commit()
        return count

    def get_user_notifications(
        self, user_id: int, limit: int = 50, unread_only: bool = False
    ) -> List[Dict]:
        """Get notifications for a user"""
        query = db.session.query(Notification).filter(Notification.user_id == user_id)

        if unread_only:
            query = query.filter(Notification.is_read == False)

        notifications = query.order_by(desc(Notification.created_at)).limit(limit).all()

        return [
            {
                "id": n.id,
                "type": n.type.value,
                "priority": n.priority.value,
                "title": n.title,
                "message": n.message,
                "data": n.data,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
                "read_at": n.read_at.isoformat() if n.read_at else None,
            }
            for n in notifications
        ]

    def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications"""
        return (
            db.session.query(Notification)
            .filter(and_(Notification.user_id == user_id, Notification.is_read == False))
            .count()
        )

    def create_job_notification(self, job: Job, notification_type: NotificationType):
        """Create job-related notifications"""
        notifications_to_create = []

        if notification_type == NotificationType.JOB_CREATED:
            # Notify potential providers about new job
            notifications_to_create.append(
                {
                    "user_id": job.customer_id,
                    "title": "Job Posted Successfully",
                    "message": f'Your job "{job.title}" has been posted and is now visible to providers.',
                    "priority": NotificationPriority.MEDIUM,
                    "data": {"job_id": job.id, "job_title": job.title},
                }
            )

        elif notification_type == NotificationType.JOB_ACCEPTED and job.provider_id:
            # Notify customer that job was accepted
            notifications_to_create.append(
                {
                    "user_id": job.customer_id,
                    "title": "Job Accepted!",
                    "message": f'A provider has accepted your job "{job.title}". Work will begin soon.',
                    "priority": NotificationPriority.HIGH,
                    "data": {"job_id": job.id, "provider_id": job.provider_id},
                }
            )

            # Notify provider about acceptance confirmation
            notifications_to_create.append(
                {
                    "user_id": job.provider_id,
                    "title": "Job Confirmed",
                    "message": f'You have successfully accepted the job "{job.title}". Contact the customer to coordinate.',
                    "priority": NotificationPriority.HIGH,
                    "data": {"job_id": job.id, "customer_id": job.customer_id},
                }
            )

        elif notification_type == NotificationType.JOB_COMPLETED:
            # Notify both parties about completion
            notifications_to_create.extend(
                [
                    {
                        "user_id": job.customer_id,
                        "title": "Job Completed!",
                        "message": f'The job "{job.title}" has been marked as completed. Please review the work.',
                        "priority": NotificationPriority.HIGH,
                        "data": {"job_id": job.id, "action_required": "review"},
                    },
                    {
                        "user_id": job.provider_id,
                        "title": "Job Completed",
                        "message": f'You have successfully completed "{job.title}". Payment will be processed soon.',
                        "priority": NotificationPriority.HIGH,
                        "data": {"job_id": job.id, "status": "awaiting_payment"},
                    },
                ]
            )

        # Create all notifications
        for notification_data in notifications_to_create:
            self.create_notification(
                user_id=notification_data["user_id"],
                notification_type=notification_type,
                title=notification_data["title"],
                message=notification_data["message"],
                priority=notification_data["priority"],
                data=notification_data["data"],
            )

    def create_smart_match_notification(self, job_id: int, provider_id: int, match_score: float):
        """Create notification for smart matching results"""
        job = db.session.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        confidence_level = (
            "High" if match_score >= 0.8 else "Medium" if match_score >= 0.6 else "Low"
        )

        self.create_notification(
            user_id=provider_id,
            notification_type=NotificationType.JOB_MATCHED,
            title=f"Perfect Job Match Found! ({confidence_level} Confidence)",
            message=f'We found a great match for you: "{job.title}". Match score: {match_score:.1%}',
            priority=(
                NotificationPriority.HIGH if match_score >= 0.8 else NotificationPriority.MEDIUM
            ),
            data={
                "job_id": job_id,
                "match_score": match_score,
                "confidence_level": confidence_level,
                "action_required": "view_job",
            },
        )


# Initialize notification manager
notification_manager = NotificationManager()


@notifications_bp.route("/list", methods=["GET"])
def get_notifications():
    """Get notifications for the current user"""
    try:
        # In a real app, get user_id from authentication
        user_id = request.args.get("user_id", type=int)
        if not user_id:
            return jsonify({"success": False, "error": "user_id is required"}), 400

        limit = request.args.get("limit", 50, type=int)
        unread_only = request.args.get("unread_only", False, type=bool)

        notifications = notification_manager.get_user_notifications(
            user_id=user_id, limit=limit, unread_only=unread_only
        )

        unread_count = notification_manager.get_unread_count(user_id)

        return jsonify(
            {
                "success": True,
                "notifications": notifications,
                "unread_count": unread_count,
                "total_returned": len(notifications),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@notifications_bp.route("/mark-read/<int:notification_id>", methods=["POST"])
def mark_notification_read(notification_id):
    """Mark a specific notification as read"""
    try:
        user_id = (
            request.json.get("user_id") if request.json else request.args.get("user_id", type=int)
        )
        if not user_id:
            return jsonify({"success": False, "error": "user_id is required"}), 400

        success = notification_manager.mark_as_read(notification_id, user_id)

        if success:
            return jsonify({"success": True, "message": "Notification marked as read"})
        else:
            return (
                jsonify({"success": False, "error": "Notification not found or already read"}),
                404,
            )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@notifications_bp.route("/mark-all-read", methods=["POST"])
def mark_all_notifications_read():
    """Mark all notifications as read for the current user"""
    try:
        user_id = (
            request.json.get("user_id") if request.json else request.args.get("user_id", type=int)
        )
        if not user_id:
            return jsonify({"success": False, "error": "user_id is required"}), 400

        count = notification_manager.mark_all_as_read(user_id)

        return jsonify({"success": True, "message": f"Marked {count} notifications as read"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@notifications_bp.route("/create", methods=["POST"])
def create_notification():
    """Create a new notification (admin/system use)"""
    try:
        data = request.get_json()

        required_fields = ["user_id", "type", "title", "message"]
        for field in required_fields:
            if field not in data:
                return jsonify({"success": False, "error": f"{field} is required"}), 400

        notification_type = NotificationType(data["type"])
        priority = NotificationPriority(data.get("priority", "medium"))

        notification = notification_manager.create_notification(
            user_id=data["user_id"],
            notification_type=notification_type,
            title=data["title"],
            message=data["message"],
            priority=priority,
            data=data.get("data", {}),
        )

        return jsonify(
            {
                "success": True,
                "notification_id": notification.id,
                "message": "Notification created successfully",
            }
        )

    except ValueError as e:
        return (
            jsonify(
                {"success": False, "error": f"Invalid notification type or priority: {str(e)}"}
            ),
            400,
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@notifications_bp.route("/stats", methods=["GET"])
def get_notification_stats():
    """Get notification statistics"""
    try:
        user_id = request.args.get("user_id", type=int)

        if user_id:
            # User-specific stats
            total_notifications = (
                db.session.query(Notification).filter(Notification.user_id == user_id).count()
            )

            unread_count = notification_manager.get_unread_count(user_id)

            # Get notifications by type
            type_counts = {}
            for notification_type in NotificationType:
                count = (
                    db.session.query(Notification)
                    .filter(
                        and_(
                            Notification.user_id == user_id, Notification.type == notification_type
                        )
                    )
                    .count()
                )
                type_counts[notification_type.value] = count

            return jsonify(
                {
                    "success": True,
                    "user_stats": {
                        "total_notifications": total_notifications,
                        "unread_count": unread_count,
                        "read_count": total_notifications - unread_count,
                        "notifications_by_type": type_counts,
                    },
                }
            )
        else:
            # Platform-wide stats
            total_notifications = db.session.query(Notification).count()
            total_unread = (
                db.session.query(Notification).filter(Notification.is_read == False).count()
            )

            # Recent activity (last 24 hours)
            recent_notifications = (
                db.session.query(Notification)
                .filter(Notification.created_at >= datetime.utcnow() - timedelta(hours=24))
                .count()
            )

            return jsonify(
                {
                    "success": True,
                    "platform_stats": {
                        "total_notifications": total_notifications,
                        "total_unread": total_unread,
                        "recent_24h": recent_notifications,
                        "read_rate_percent": (
                            round(
                                (total_notifications - total_unread) / total_notifications * 100, 2
                            )
                            if total_notifications > 0
                            else 0
                        ),
                    },
                }
            )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# WebSocket event handlers (if using Flask-SocketIO)
def init_socketio_events(socketio):
    """Initialize WebSocket event handlers"""
    notification_manager.socketio = socketio

    @socketio.on("connect")
    def handle_connect():
        print("Client connected")

    @socketio.on("disconnect")
    def handle_disconnect():
        print("Client disconnected")

    @socketio.on("join_user_room")
    def handle_join_user_room(data):
        user_id = data.get("user_id")
        if user_id:
            room = f"user_{user_id}"
            join_room(room)
            emit("joined_room", {"room": room})

    @socketio.on("leave_user_room")
    def handle_leave_user_room(data):
        user_id = data.get("user_id")
        if user_id:
            room = f"user_{user_id}"
            leave_room(room)
            emit("left_room", {"room": room})
