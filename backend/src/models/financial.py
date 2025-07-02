"""
Financial Management Models for Biped Platform
Comprehensive business management for all stakeholders
"""

from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Decimal as SQLDecimal, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from src.models.base import db

class InvoiceStatus(Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class ExpenseCategory(Enum):
    MATERIALS = "materials"
    LABOR = "labor"
    EQUIPMENT = "equipment"
    TRANSPORT = "transport"
    INSURANCE = "insurance"
    MARKETING = "marketing"
    OFFICE = "office"
    OTHER = "other"

class Invoice(db.Model):
    """Professional invoice management"""
    __tablename__ = 'invoices'
    
    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=True)
    
    # Client Information
    client_name = Column(String(200), nullable=False)
    client_email = Column(String(200), nullable=False)
    client_address = Column(Text, nullable=True)
    client_phone = Column(String(50), nullable=True)
    
    # Invoice Details
    issue_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False)
    status = Column(String(20), default=InvoiceStatus.DRAFT.value)
    
    # Financial Information
    subtotal = Column(SQLDecimal(10, 2), nullable=False)
    tax_rate = Column(SQLDecimal(5, 2), default=Decimal('10.00'))  # GST
    tax_amount = Column(SQLDecimal(10, 2), nullable=False)
    total_amount = Column(SQLDecimal(10, 2), nullable=False)
    
    # Payment Information
    payment_terms = Column(String(100), default="Net 30")
    payment_method = Column(String(50), nullable=True)
    payment_date = Column(DateTime, nullable=True)
    payment_reference = Column(String(100), nullable=True)
    
    # Line Items (JSON for flexibility)
    line_items = Column(JSON, nullable=False)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    terms_conditions = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="invoices")
    job = relationship("Job", back_populates="invoices")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        if not self.due_date:
            self.due_date = self.issue_date + timedelta(days=30)
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d")
        count = Invoice.query.filter(Invoice.invoice_number.like(f"INV-{timestamp}%")).count()
        return f"INV-{timestamp}-{count + 1:04d}"
    
    def calculate_totals(self):
        """Calculate invoice totals from line items"""
        self.subtotal = sum(Decimal(str(item['quantity'])) * Decimal(str(item['rate'])) 
                           for item in self.line_items)
        self.tax_amount = self.subtotal * (self.tax_rate / 100)
        self.total_amount = self.subtotal + self.tax_amount
    
    def mark_as_paid(self, payment_method=None, payment_reference=None):
        """Mark invoice as paid"""
        self.status = InvoiceStatus.PAID.value
        self.payment_date = datetime.utcnow()
        self.payment_method = payment_method
        self.payment_reference = payment_reference
    
    def is_overdue(self):
        """Check if invoice is overdue"""
        return (self.status != InvoiceStatus.PAID.value and 
                self.due_date < datetime.utcnow())
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'client_name': self.client_name,
            'client_email': self.client_email,
            'issue_date': self.issue_date.isoformat(),
            'due_date': self.due_date.isoformat(),
            'status': self.status,
            'subtotal': float(self.subtotal),
            'tax_amount': float(self.tax_amount),
            'total_amount': float(self.total_amount),
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'line_items': self.line_items,
            'is_overdue': self.is_overdue()
        }

class Quote(db.Model):
    """Professional quote management"""
    __tablename__ = 'quotes'
    
    id = Column(Integer, primary_key=True)
    quote_number = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=True)
    
    # Client Information
    client_name = Column(String(200), nullable=False)
    client_email = Column(String(200), nullable=False)
    client_phone = Column(String(50), nullable=True)
    project_address = Column(Text, nullable=False)
    
    # Quote Details
    issue_date = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=False)
    status = Column(String(20), default="draft")  # draft, sent, accepted, rejected, expired
    
    # Project Information
    project_title = Column(String(200), nullable=False)
    project_description = Column(Text, nullable=False)
    estimated_duration = Column(String(100), nullable=True)
    start_date = Column(DateTime, nullable=True)
    
    # Financial Information
    subtotal = Column(SQLDecimal(10, 2), nullable=False)
    tax_rate = Column(SQLDecimal(5, 2), default=Decimal('10.00'))
    tax_amount = Column(SQLDecimal(10, 2), nullable=False)
    total_amount = Column(SQLDecimal(10, 2), nullable=False)
    
    # Quote Items (JSON for flexibility)
    quote_items = Column(JSON, nullable=False)
    
    # Terms and Conditions
    payment_terms = Column(Text, nullable=True)
    terms_conditions = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # AI Analysis Results
    ai_analysis = Column(JSON, nullable=True)
    confidence_score = Column(SQLDecimal(3, 2), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="quotes")
    job = relationship("Job", back_populates="quotes")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.quote_number:
            self.quote_number = self.generate_quote_number()
        if not self.valid_until:
            self.valid_until = self.issue_date + timedelta(days=30)
    
    def generate_quote_number(self):
        """Generate unique quote number"""
        timestamp = datetime.now().strftime("%Y%m%d")
        count = Quote.query.filter(Quote.quote_number.like(f"QUO-{timestamp}%")).count()
        return f"QUO-{timestamp}-{count + 1:04d}"
    
    def calculate_totals(self):
        """Calculate quote totals from items"""
        self.subtotal = sum(Decimal(str(item['quantity'])) * Decimal(str(item['rate'])) 
                           for item in self.quote_items)
        self.tax_amount = self.subtotal * (self.tax_rate / 100)
        self.total_amount = self.subtotal + self.tax_amount
    
    def is_expired(self):
        """Check if quote has expired"""
        return self.valid_until < datetime.utcnow()
    
    def accept_quote(self):
        """Accept the quote and create job"""
        self.status = "accepted"
        # TODO: Create job from accepted quote
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'quote_number': self.quote_number,
            'client_name': self.client_name,
            'project_title': self.project_title,
            'issue_date': self.issue_date.isoformat(),
            'valid_until': self.valid_until.isoformat(),
            'status': self.status,
            'subtotal': float(self.subtotal),
            'tax_amount': float(self.tax_amount),
            'total_amount': float(self.total_amount),
            'quote_items': self.quote_items,
            'is_expired': self.is_expired(),
            'confidence_score': float(self.confidence_score) if self.confidence_score else None
        }

class Expense(db.Model):
    """Expense tracking and management"""
    __tablename__ = 'expenses'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=True)
    
    # Expense Details
    description = Column(String(500), nullable=False)
    category = Column(String(50), nullable=False)
    amount = Column(SQLDecimal(10, 2), nullable=False)
    expense_date = Column(DateTime, nullable=False)
    
    # Receipt Information
    receipt_url = Column(String(500), nullable=True)
    receipt_analysis = Column(JSON, nullable=True)  # AI analysis results
    
    # Tax Information
    is_tax_deductible = Column(Boolean, default=True)
    tax_category = Column(String(100), nullable=True)
    gst_amount = Column(SQLDecimal(10, 2), nullable=True)
    
    # Vendor Information
    vendor_name = Column(String(200), nullable=True)
    vendor_abn = Column(String(20), nullable=True)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # For custom categorization
    
    # Approval Workflow
    is_approved = Column(Boolean, default=True)
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="expenses")
    job = relationship("Job", back_populates="expenses")
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'description': self.description,
            'category': self.category,
            'amount': float(self.amount),
            'expense_date': self.expense_date.isoformat(),
            'is_tax_deductible': self.is_tax_deductible,
            'vendor_name': self.vendor_name,
            'gst_amount': float(self.gst_amount) if self.gst_amount else None,
            'is_approved': self.is_approved,
            'tags': self.tags
        }

class PlatformRevenue(db.Model):
    """Platform revenue tracking for owner dashboard"""
    __tablename__ = 'platform_revenue'
    
    id = Column(Integer, primary_key=True)
    
    # Transaction Details
    transaction_type = Column(String(50), nullable=False)  # commission, subscription, service_fee
    source_type = Column(String(50), nullable=False)  # job, subscription, marketplace
    source_id = Column(Integer, nullable=False)  # ID of the source record
    
    # Financial Information
    gross_amount = Column(SQLDecimal(10, 2), nullable=False)  # Total transaction amount
    commission_rate = Column(SQLDecimal(5, 2), nullable=False)  # Commission percentage
    commission_amount = Column(SQLDecimal(10, 2), nullable=False)  # Platform commission
    net_amount = Column(SQLDecimal(10, 2), nullable=False)  # Amount to provider
    
    # User Information
    provider_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Payment Information
    payment_status = Column(String(20), default="pending")  # pending, completed, failed
    payment_date = Column(DateTime, nullable=True)
    payment_method = Column(String(50), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    provider = relationship("User", foreign_keys=[provider_id])
    customer = relationship("User", foreign_keys=[customer_id])
    
    @classmethod
    def calculate_total_revenue(cls, start_date=None, end_date=None):
        """Calculate total platform revenue"""
        query = cls.query.filter(cls.payment_status == "completed")
        
        if start_date:
            query = query.filter(cls.payment_date >= start_date)
        if end_date:
            query = query.filter(cls.payment_date <= end_date)
        
        return query.with_entities(db.func.sum(cls.commission_amount)).scalar() or Decimal('0')
    
    @classmethod
    def get_revenue_breakdown(cls, start_date=None, end_date=None):
        """Get revenue breakdown by type"""
        query = cls.query.filter(cls.payment_status == "completed")
        
        if start_date:
            query = query.filter(cls.payment_date >= start_date)
        if end_date:
            query = query.filter(cls.payment_date <= end_date)
        
        breakdown = query.with_entities(
            cls.transaction_type,
            db.func.sum(cls.commission_amount).label('total'),
            db.func.count(cls.id).label('count')
        ).group_by(cls.transaction_type).all()
        
        return [{'type': b.transaction_type, 'total': float(b.total), 'count': b.count} 
                for b in breakdown]
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'transaction_type': self.transaction_type,
            'source_type': self.source_type,
            'gross_amount': float(self.gross_amount),
            'commission_rate': float(self.commission_rate),
            'commission_amount': float(self.commission_amount),
            'payment_status': self.payment_status,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'created_at': self.created_at.isoformat()
        }

class FinancialReport(db.Model):
    """Generated financial reports"""
    __tablename__ = 'financial_reports'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Report Details
    report_type = Column(String(50), nullable=False)  # monthly, quarterly, annual, custom
    report_period_start = Column(DateTime, nullable=False)
    report_period_end = Column(DateTime, nullable=False)
    
    # Report Data (JSON for flexibility)
    report_data = Column(JSON, nullable=False)
    
    # File Information
    file_url = Column(String(500), nullable=True)  # PDF report URL
    file_size = Column(Integer, nullable=True)
    
    # Metadata
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="financial_reports")
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'report_type': self.report_type,
            'period_start': self.report_period_start.isoformat(),
            'period_end': self.report_period_end.isoformat(),
            'file_url': self.file_url,
            'generated_at': self.generated_at.isoformat()
        }

