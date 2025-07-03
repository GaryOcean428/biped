from datetime import datetime

from src.models.user import db


class Review(db.Model):
    """Reviews and ratings for completed jobs"""

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Overall rating
    overall_rating = db.Column(db.Integer, nullable=False)  # 1-5 stars

    # Detailed ratings
    quality_rating = db.Column(db.Integer, nullable=True)  # 1-5 stars
    communication_rating = db.Column(db.Integer, nullable=True)  # 1-5 stars
    timeliness_rating = db.Column(db.Integer, nullable=True)  # 1-5 stars
    professionalism_rating = db.Column(db.Integer, nullable=True)  # 1-5 stars
    value_rating = db.Column(db.Integer, nullable=True)  # 1-5 stars

    # Review content
    title = db.Column(db.String(200), nullable=True)
    comment = db.Column(db.Text, nullable=True)

    # Additional information
    would_recommend = db.Column(db.Boolean, nullable=True)
    would_hire_again = db.Column(db.Boolean, nullable=True)

    # Review metadata
    is_verified = db.Column(db.Boolean, default=True)  # Verified through completed job
    is_public = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)

    # Response from reviewee
    response = db.Column(db.Text, nullable=True)
    response_date = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    reviewer = db.relationship("User", foreign_keys=[reviewer_id], backref="reviews_given")
    reviewee = db.relationship("User", foreign_keys=[reviewee_id], backref="reviews_received")

    def __repr__(self):
        return f"<Review {self.id} - {self.overall_rating} stars>"

    def get_average_detailed_rating(self):
        """Calculate average of detailed ratings"""
        ratings = [
            self.quality_rating,
            self.communication_rating,
            self.timeliness_rating,
            self.professionalism_rating,
            self.value_rating,
        ]
        valid_ratings = [r for r in ratings if r is not None]
        return sum(valid_ratings) / len(valid_ratings) if valid_ratings else None

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "reviewer_id": self.reviewer_id,
            "reviewee_id": self.reviewee_id,
            "overall_rating": self.overall_rating,
            "quality_rating": self.quality_rating,
            "communication_rating": self.communication_rating,
            "timeliness_rating": self.timeliness_rating,
            "professionalism_rating": self.professionalism_rating,
            "value_rating": self.value_rating,
            "average_detailed_rating": self.get_average_detailed_rating(),
            "title": self.title,
            "comment": self.comment,
            "would_recommend": self.would_recommend,
            "would_hire_again": self.would_hire_again,
            "is_verified": self.is_verified,
            "is_public": self.is_public,
            "is_featured": self.is_featured,
            "response": self.response,
            "response_date": self.response_date.isoformat() if self.response_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "reviewer_name": self.reviewer.get_full_name() if self.reviewer else None,
            "reviewee_name": self.reviewee.get_full_name() if self.reviewee else None,
            "job_title": self.job.title if self.job else None,
        }


class Message(db.Model):
    """General messaging between users"""

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Message content
    subject = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=False)
    attachments = db.Column(db.JSON, nullable=True)  # Array of file URLs

    # Message metadata
    is_read = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    is_system_message = db.Column(db.Boolean, default=False)

    # Threading
    thread_id = db.Column(db.String(100), nullable=True)  # For grouping related messages
    reply_to_id = db.Column(db.Integer, db.ForeignKey("message.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    replies = db.relationship("Message", backref=db.backref("reply_to", remote_side=[id]))

    def __repr__(self):
        return f"<Message {self.id}>"

    def mark_as_read(self):
        """Mark message as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()

    def to_dict(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "subject": self.subject,
            "message": self.message,
            "attachments": self.attachments,
            "is_read": self.is_read,
            "is_archived": self.is_archived,
            "is_system_message": self.is_system_message,
            "thread_id": self.thread_id,
            "reply_to_id": self.reply_to_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "sender_name": self.sender.get_full_name() if self.sender else None,
            "recipient_name": self.recipient.get_full_name() if self.recipient else None,
        }


class Notification(db.Model):
    """System notifications for users"""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Notification content
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(
        db.String(50), nullable=False
    )  # 'job_update', 'new_message', 'payment', etc.

    # Related entities
    related_job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=True)
    related_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    # Action URL
    action_url = db.Column(db.String(500), nullable=True)

    # Status
    is_read = db.Column(db.Boolean, default=False)
    is_sent = db.Column(db.Boolean, default=False)  # For email/SMS notifications

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship("User", foreign_keys=[user_id], backref="notifications")
    related_job = db.relationship("Job", foreign_keys=[related_job_id])
    related_user = db.relationship("User", foreign_keys=[related_user_id])

    def __repr__(self):
        return f"<Notification {self.title}>"

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "notification_type": self.notification_type,
            "related_job_id": self.related_job_id,
            "related_user_id": self.related_user_id,
            "action_url": self.action_url,
            "is_read": self.is_read,
            "is_sent": self.is_sent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
        }
