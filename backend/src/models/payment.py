from datetime import datetime

from .user import db


class StripeAccount(db.Model):
    """Stripe Connect account information for service providers"""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    stripe_account_id = db.Column(db.String(255), unique=True, nullable=False)
    account_type = db.Column(
        db.String(50), default="express"
    )  # express, standard, custom
    charges_enabled = db.Column(db.Boolean, default=False)
    payouts_enabled = db.Column(db.Boolean, default=False)
    details_submitted = db.Column(db.Boolean, default=False)
    requirements_due = db.Column(db.Text)  # JSON string of requirements
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship
    user = db.relationship("User", backref="stripe_account")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "stripe_account_id": self.stripe_account_id,
            "account_type": self.account_type,
            "charges_enabled": self.charges_enabled,
            "payouts_enabled": self.payouts_enabled,
            "details_submitted": self.details_submitted,
            "requirements_due": self.requirements_due,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Payment(db.Model):
    """Payment transactions for jobs"""

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Stripe payment information
    stripe_payment_intent_id = db.Column(db.String(255), unique=True, nullable=False)
    stripe_charge_id = db.Column(db.String(255))

    # Payment amounts (in cents)
    total_amount = db.Column(
        db.Integer, nullable=False
    )  # Total amount paid by customer
    platform_fee = db.Column(db.Integer, nullable=False)  # Platform fee (5-10%)
    provider_amount = db.Column(
        db.Integer, nullable=False
    )  # Amount to transfer to provider

    # Payment status
    status = db.Column(
        db.String(50), default="pending"
    )  # pending, paid, transferred, refunded, disputed
    payment_method = db.Column(db.String(50))  # card, bank_transfer, etc.

    # Escrow management
    escrow_released = db.Column(db.Boolean, default=False)
    escrow_release_date = db.Column(db.DateTime)
    auto_release_date = db.Column(db.DateTime)  # Auto-release after X days

    # Metadata
    description = db.Column(db.Text)
    meta_data = db.Column(db.Text)  # JSON string for additional data

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)
    transferred_at = db.Column(db.DateTime)

    # Relationships
    job = db.relationship("Job", backref="payments")
    customer = db.relationship(
        "User", foreign_keys=[customer_id], backref="customer_payments"
    )
    provider = db.relationship(
        "User", foreign_keys=[provider_id], backref="provider_payments"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "customer_id": self.customer_id,
            "provider_id": self.provider_id,
            "stripe_payment_intent_id": self.stripe_payment_intent_id,
            "stripe_charge_id": self.stripe_charge_id,
            "total_amount": self.total_amount,
            "platform_fee": self.platform_fee,
            "provider_amount": self.provider_amount,
            "status": self.status,
            "payment_method": self.payment_method,
            "escrow_released": self.escrow_released,
            "escrow_release_date": (
                self.escrow_release_date.isoformat()
                if self.escrow_release_date
                else None
            ),
            "auto_release_date": (
                self.auto_release_date.isoformat() if self.auto_release_date else None
            ),
            "description": self.description,
            "meta_data": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "transferred_at": (
                self.transferred_at.isoformat() if self.transferred_at else None
            ),
        }


class Transfer(db.Model):
    """Transfers from platform to service providers"""

    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey("payment.id"), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    stripe_account_id = db.Column(db.String(255), nullable=False)

    # Transfer details
    stripe_transfer_id = db.Column(db.String(255), unique=True, nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # Amount transferred (in cents)
    currency = db.Column(db.String(3), default="USD")

    # Status and metadata
    status = db.Column(
        db.String(50), default="pending"
    )  # pending, paid, failed, canceled
    failure_reason = db.Column(db.String(255))
    description = db.Column(db.Text)
    meta_data = db.Column(db.Text)  # JSON string

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    transferred_at = db.Column(db.DateTime)

    # Relationships
    payment = db.relationship("Payment", backref="transfers")
    provider = db.relationship("User", backref="transfers")

    def to_dict(self):
        return {
            "id": self.id,
            "payment_id": self.payment_id,
            "provider_id": self.provider_id,
            "stripe_account_id": self.stripe_account_id,
            "stripe_transfer_id": self.stripe_transfer_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "failure_reason": self.failure_reason,
            "description": self.description,
            "meta_data": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "transferred_at": (
                self.transferred_at.isoformat() if self.transferred_at else None
            ),
        }


class Dispute(db.Model):
    """Payment disputes and chargebacks"""

    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey("payment.id"), nullable=False)
    stripe_dispute_id = db.Column(db.String(255), unique=True, nullable=False)

    # Dispute details
    amount = db.Column(db.Integer, nullable=False)  # Disputed amount (in cents)
    currency = db.Column(db.String(3), default="USD")
    reason = db.Column(
        db.String(100)
    )  # duplicate, fraudulent, subscription_canceled, etc.
    status = db.Column(
        db.String(50)
    )  # warning_needs_response, warning_under_review, warning_closed, etc.

    # Evidence and resolution
    evidence_due_by = db.Column(db.DateTime)
    evidence_submitted = db.Column(db.Boolean, default=False)
    is_charge_refundable = db.Column(db.Boolean, default=True)

    # Metadata
    meta_data = db.Column(db.Text)  # JSON string

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship
    payment = db.relationship("Payment", backref="disputes")

    def to_dict(self):
        return {
            "id": self.id,
            "payment_id": self.payment_id,
            "stripe_dispute_id": self.stripe_dispute_id,
            "amount": self.amount,
            "currency": self.currency,
            "reason": self.reason,
            "status": self.status,
            "evidence_due_by": (
                self.evidence_due_by.isoformat() if self.evidence_due_by else None
            ),
            "evidence_submitted": self.evidence_submitted,
            "is_charge_refundable": self.is_charge_refundable,
            "meta_data": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
