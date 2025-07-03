"""
Financial Management API Routes for Biped Platform
Complete business management for all stakeholders
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO

import requests
from ai_engine import BipedAIEngine
from flask import Blueprint, jsonify, request, send_file
from flask_login import current_user, login_required
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from src.models.financial import Expense, FinancialQuote, FinancialReport, Invoice, PlatformRevenue
from src.models.user import db

financial_bp = Blueprint("financial", __name__, url_prefix="/api/financial")

# ============================================================================
# INVOICE MANAGEMENT
# ============================================================================


@financial_bp.route("/invoices", methods=["GET"])
@login_required
def get_invoices():
    """Get user's invoices with filtering and pagination"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        status = request.args.get("status")

        query = Invoice.query.filter_by(user_id=current_user.id)

        if status:
            query = query.filter_by(status=status)

        invoices = query.order_by(Invoice.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify(
            {
                "success": True,
                "invoices": [invoice.to_dict() for invoice in invoices.items],
                "pagination": {
                    "page": page,
                    "pages": invoices.pages,
                    "per_page": per_page,
                    "total": invoices.total,
                },
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@financial_bp.route("/invoices", methods=["POST"])
@login_required
def create_invoice():
    """Create new invoice with AI assistance"""
    try:
        data = request.get_json()

        # Create invoice
        invoice = Invoice(
            user_id=current_user.id,
            job_id=data.get("job_id"),
            client_name=data["client_name"],
            client_email=data["client_email"],
            client_address=data.get("client_address"),
            client_phone=data.get("client_phone"),
            line_items=data["line_items"],
            payment_terms=data.get("payment_terms", "Net 30"),
            notes=data.get("notes"),
            terms_conditions=data.get("terms_conditions"),
        )

        # Calculate totals
        invoice.calculate_totals()

        db.session.add(invoice)
        db.session.commit()

        # Trigger N8N workflow for invoice creation
        trigger_n8n_workflow(
            "invoice_created",
            {
                "invoice_id": invoice.id,
                "client_email": invoice.client_email,
                "total_amount": float(invoice.total_amount),
                "due_date": invoice.due_date.isoformat(),
            },
        )

        return (
            jsonify(
                {
                    "success": True,
                    "invoice": invoice.to_dict(),
                    "message": "Invoice created successfully",
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@financial_bp.route("/invoices/<int:invoice_id>/pdf", methods=["GET"])
@login_required
def generate_invoice_pdf(invoice_id):
    """Generate professional PDF invoice"""
    try:
        invoice = Invoice.query.filter_by(id=invoice_id, user_id=current_user.id).first()
        if not invoice:
            return jsonify({"success": False, "error": "Invoice not found"}), 404

        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Header
        header_style = ParagraphStyle(
            "CustomHeader",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1e40af"),
            spaceAfter=30,
        )
        story.append(Paragraph("INVOICE", header_style))

        # Invoice details
        invoice_data = [
            ["Invoice Number:", invoice.invoice_number],
            ["Issue Date:", invoice.issue_date.strftime("%d/%m/%Y")],
            ["Due Date:", invoice.due_date.strftime("%d/%m/%Y")],
            ["Status:", invoice.status.upper()],
        ]

        invoice_table = Table(invoice_data, colWidths=[2 * inch, 2 * inch])
        invoice_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )
        story.append(invoice_table)
        story.append(Spacer(1, 20))

        # Client information
        story.append(Paragraph("Bill To:", styles["Heading2"]))
        client_info = f"""
        {invoice.client_name}<br/>
        {invoice.client_email}<br/>
        {invoice.client_address or ''}<br/>
        {invoice.client_phone or ''}
        """
        story.append(Paragraph(client_info, styles["Normal"]))
        story.append(Spacer(1, 20))

        # Line items
        items_data = [["Description", "Quantity", "Rate", "Amount"]]
        for item in invoice.line_items:
            amount = Decimal(str(item["quantity"])) * Decimal(str(item["rate"]))
            items_data.append(
                [
                    item["description"],
                    str(item["quantity"]),
                    f"${item['rate']:.2f}",
                    f"${amount:.2f}",
                ]
            )

        # Totals
        items_data.extend(
            [
                ["", "", "Subtotal:", f"${invoice.subtotal:.2f}"],
                ["", "", f"Tax ({invoice.tax_rate}%):", f"${invoice.tax_amount:.2f}"],
                ["", "", "Total:", f"${invoice.total_amount:.2f}"],
            ]
        )

        items_table = Table(items_data, colWidths=[3 * inch, 1 * inch, 1 * inch, 1 * inch])
        items_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 14),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTNAME", (0, -3), (-1, -1), "Helvetica-Bold"),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#0d9488")),
                    ("TEXTCOLOR", (0, -1), (-1, -1), colors.whitesmoke),
                ]
            )
        )
        story.append(items_table)

        # Payment terms and notes
        if invoice.notes:
            story.append(Spacer(1, 20))
            story.append(Paragraph("Notes:", styles["Heading3"]))
            story.append(Paragraph(invoice.notes, styles["Normal"]))

        doc.build(story)
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"invoice_{invoice.invoice_number}.pdf",
            mimetype="application/pdf",
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@financial_bp.route("/invoices/<int:invoice_id>/send", methods=["POST"])
@login_required
def send_invoice(invoice_id):
    """Send invoice via email using N8N workflow"""
    try:
        invoice = Invoice.query.filter_by(id=invoice_id, user_id=current_user.id).first()
        if not invoice:
            return jsonify({"success": False, "error": "Invoice not found"}), 404

        # Update status
        invoice.status = "sent"
        db.session.commit()

        # Trigger N8N email workflow
        trigger_n8n_workflow(
            "send_invoice_email",
            {
                "invoice_id": invoice.id,
                "client_email": invoice.client_email,
                "client_name": invoice.client_name,
                "invoice_number": invoice.invoice_number,
                "total_amount": float(invoice.total_amount),
                "due_date": invoice.due_date.isoformat(),
                "provider_name": current_user.name,
            },
        )

        return jsonify({"success": True, "message": "Invoice sent successfully"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# QUOTE MANAGEMENT
# ============================================================================


@financial_bp.route("/quotes", methods=["GET"])
@login_required
def get_quotes():
    """Get user's quotes with filtering"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        status = request.args.get("status")

        query = FinancialQuote.query.filter_by(user_id=current_user.id)

        if status:
            query = query.filter_by(status=status)

        quotes = query.order_by(FinancialQuote.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify(
            {
                "success": True,
                "quotes": [quote.to_dict() for quote in quotes.items],
                "pagination": {
                    "page": page,
                    "pages": quotes.pages,
                    "per_page": per_page,
                    "total": quotes.total,
                },
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@financial_bp.route("/quotes/ai-generate", methods=["POST"])
@login_required
def ai_generate_quote():
    """Generate quote using AI analysis"""
    try:
        data = request.get_json()

        # Use Flowise AI for quote generation
        ai_analysis = generate_ai_quote(data)

        # Create quote with AI suggestions
        quote = FinancialQuote(
            user_id=current_user.id,
            job_id=data.get("job_id"),
            client_name=data["client_name"],
            client_email=data["client_email"],
            client_phone=data.get("client_phone"),
            project_address=data["project_address"],
            project_title=data["project_title"],
            project_description=data["project_description"],
            estimated_duration=ai_analysis.get("estimated_duration"),
            quote_items=ai_analysis["quote_items"],
            ai_analysis=ai_analysis,
            confidence_score=ai_analysis.get("confidence_score"),
            payment_terms=ai_analysis.get("payment_terms"),
            terms_conditions=ai_analysis.get("terms_conditions"),
        )

        # Calculate totals
        quote.calculate_totals()

        db.session.add(quote)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "quote": quote.to_dict(),
                    "ai_insights": ai_analysis.get("insights", []),
                    "message": "AI-powered quote generated successfully",
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# EXPENSE MANAGEMENT
# ============================================================================


@financial_bp.route("/expenses", methods=["GET"])
@login_required
def get_expenses():
    """Get user's expenses with filtering"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        category = request.args.get("category")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        query = Expense.query.filter_by(user_id=current_user.id)

        if category:
            query = query.filter_by(category=category)

        if start_date:
            query = query.filter(Expense.expense_date >= datetime.fromisoformat(start_date))

        if end_date:
            query = query.filter(Expense.expense_date <= datetime.fromisoformat(end_date))

        expenses = query.order_by(Expense.expense_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # Calculate totals
        total_amount = sum(expense.amount for expense in expenses.items)
        tax_deductible_amount = sum(
            expense.amount for expense in expenses.items if expense.is_tax_deductible
        )

        return jsonify(
            {
                "success": True,
                "expenses": [expense.to_dict() for expense in expenses.items],
                "summary": {
                    "total_amount": float(total_amount),
                    "tax_deductible_amount": float(tax_deductible_amount),
                    "count": expenses.total,
                },
                "pagination": {
                    "page": page,
                    "pages": expenses.pages,
                    "per_page": per_page,
                    "total": expenses.total,
                },
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@financial_bp.route("/expenses", methods=["POST"])
@login_required
def create_expense():
    """Create new expense with AI categorization"""
    try:
        data = request.get_json()

        # AI categorization if description provided
        ai_analysis = None
        if data.get("description"):
            ai_analysis = analyze_expense_with_ai(data["description"])

        expense = Expense(
            user_id=current_user.id,
            job_id=data.get("job_id"),
            description=data["description"],
            category=ai_analysis.get("category", data.get("category", "other")),
            amount=Decimal(str(data["amount"])),
            expense_date=datetime.fromisoformat(data["expense_date"]),
            vendor_name=data.get("vendor_name"),
            vendor_abn=data.get("vendor_abn"),
            is_tax_deductible=ai_analysis.get(
                "is_tax_deductible", data.get("is_tax_deductible", True)
            ),
            tax_category=ai_analysis.get("tax_category"),
            gst_amount=Decimal(str(data["gst_amount"])) if data.get("gst_amount") else None,
            notes=data.get("notes"),
            tags=data.get("tags", []),
        )

        if ai_analysis:
            expense.receipt_analysis = ai_analysis

        db.session.add(expense)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "expense": expense.to_dict(),
                    "ai_suggestions": ai_analysis.get("suggestions", []) if ai_analysis else [],
                    "message": "Expense recorded successfully",
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# PLATFORM OWNER DASHBOARD (braden.lang77@gmail.com)
# ============================================================================


@financial_bp.route("/platform/revenue", methods=["GET"])
@login_required
def get_platform_revenue():
    """Get platform revenue analytics for owner"""
    try:
        # Check if user is platform owner
        if current_user.email != "braden.lang77@gmail.com":
            return jsonify({"success": False, "error": "Unauthorized"}), 403

        # Date range
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)

        # Calculate metrics
        total_revenue = PlatformRevenue.calculate_total_revenue(start_date, end_date)
        revenue_breakdown = PlatformRevenue.get_revenue_breakdown(start_date, end_date)

        # Monthly revenue trend
        monthly_revenue = get_monthly_revenue_trend(start_date, end_date)

        # User metrics
        user_metrics = get_user_growth_metrics()

        # Transaction metrics
        transaction_metrics = get_transaction_metrics(start_date, end_date)

        return jsonify(
            {
                "success": True,
                "revenue_summary": {
                    "total_revenue": float(total_revenue),
                    "revenue_breakdown": revenue_breakdown,
                    "monthly_trend": monthly_revenue,
                },
                "user_metrics": user_metrics,
                "transaction_metrics": transaction_metrics,
                "period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                },
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@financial_bp.route("/platform/analytics", methods=["GET"])
@login_required
def get_platform_analytics():
    """Comprehensive platform analytics for owner"""
    try:
        # Check if user is platform owner
        if current_user.email != "braden.lang77@gmail.com":
            return jsonify({"success": False, "error": "Unauthorized"}), 403

        analytics = {
            "revenue_metrics": get_revenue_metrics(),
            "user_acquisition": get_user_acquisition_metrics(),
            "job_completion_rates": get_job_completion_metrics(),
            "provider_performance": get_provider_performance_metrics(),
            "market_penetration": get_market_penetration_metrics(),
            "growth_forecasting": get_growth_forecasting(),
            "competitive_analysis": get_competitive_metrics(),
        }

        return jsonify(
            {"success": True, "analytics": analytics, "generated_at": datetime.utcnow().isoformat()}
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# N8N INTEGRATION FUNCTIONS
# ============================================================================


def trigger_n8n_workflow(workflow_name, data):
    """Trigger N8N workflow in anythingllm project"""
    try:
        # N8N webhook URL (adjust based on your anythingllm setup)
        n8n_webhook_url = f"https://anythingllm.up.railway.app/webhook/{workflow_name}"

        payload = {
            "workflow": workflow_name,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "biped-platform",
        }

        response = requests.post(n8n_webhook_url, json=payload, timeout=10)
        return response.status_code == 200

    except Exception as e:
        print(f"N8N workflow trigger failed: {e}")
        return False


# ============================================================================
# FLOWISE AI INTEGRATION FUNCTIONS
# ============================================================================


def generate_ai_quote(quote_data):
    """Generate quote using Flowise AI"""
    try:
        # Flowise API endpoint (adjust based on your anythingllm setup)
        flowise_url = "https://anythingllm.up.railway.app/api/v1/prediction/quote-generator"

        payload = {
            "question": f"""
            Generate a professional quote for the following project:
            
            Project: {quote_data['project_title']}
            Description: {quote_data['project_description']}
            Location: {quote_data['project_address']}
            Client: {quote_data['client_name']}
            
            Please provide:
            1. Detailed quote items with quantities and rates
            2. Estimated duration
            3. Payment terms
            4. Terms and conditions
            5. Confidence score (0-1)
            6. Professional insights and recommendations
            """,
            "overrideConfig": {"temperature": 0.3, "maxTokens": 2000},
        }

        response = requests.post(flowise_url, json=payload, timeout=30)

        if response.status_code == 200:
            ai_response = response.json()
            return parse_ai_quote_response(ai_response["text"])
        else:
            # Fallback to basic quote structure
            return generate_fallback_quote(quote_data)

    except Exception as e:
        print(f"Flowise AI quote generation failed: {e}")
        return generate_fallback_quote(quote_data)


def analyze_expense_with_ai(description):
    """Analyze expense using Flowise AI"""
    try:
        flowise_url = "https://anythingllm.up.railway.app/api/v1/prediction/expense-analyzer"

        payload = {
            "question": f"""
            Analyze this expense and provide categorization:
            
            Description: {description}
            
            Please provide:
            1. Category (materials, labor, equipment, transport, insurance, marketing, office, other)
            2. Tax deductibility (true/false)
            3. Tax category for Australian business
            4. Suggestions for optimization
            """,
            "overrideConfig": {"temperature": 0.1, "maxTokens": 500},
        }

        response = requests.post(flowise_url, json=payload, timeout=15)

        if response.status_code == 200:
            ai_response = response.json()
            return parse_ai_expense_response(ai_response["text"])
        else:
            return None

    except Exception as e:
        print(f"Flowise AI expense analysis failed: {e}")
        return None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def parse_ai_quote_response(ai_text):
    """Parse AI response into structured quote data"""
    # This would parse the AI response and extract structured data
    # For now, return a basic structure
    return {
        "quote_items": [{"description": "Labor and materials", "quantity": 1, "rate": 1500.00}],
        "estimated_duration": "2-3 weeks",
        "payment_terms": "50% deposit, 50% on completion",
        "terms_conditions": "Standard terms and conditions apply",
        "confidence_score": 0.85,
        "insights": ["Project appears straightforward", "Standard pricing applies"],
    }


def parse_ai_expense_response(ai_text):
    """Parse AI expense analysis response"""
    # This would parse the AI response
    # For now, return basic categorization
    return {
        "category": "materials",
        "is_tax_deductible": True,
        "tax_category": "Business expense",
        "suggestions": ["Keep receipt for tax purposes"],
    }


def generate_fallback_quote(quote_data):
    """Generate basic quote structure as fallback"""
    return {
        "quote_items": [
            {"description": "Project work as described", "quantity": 1, "rate": 1000.00}
        ],
        "estimated_duration": "1-2 weeks",
        "payment_terms": "Net 30",
        "terms_conditions": "Standard terms apply",
        "confidence_score": 0.5,
        "insights": ["Basic quote generated - please review and adjust"],
    }


def get_monthly_revenue_trend(start_date, end_date):
    """Get monthly revenue trend data"""
    # Implementation for monthly revenue calculations
    return []


def get_user_growth_metrics():
    """Get user growth and acquisition metrics"""
    # Implementation for user metrics
    return {}


def get_transaction_metrics(start_date, end_date):
    """Get transaction analytics"""
    # Implementation for transaction metrics
    return {}


def get_revenue_metrics():
    """Get comprehensive revenue metrics"""
    return {}


def get_user_acquisition_metrics():
    """Get user acquisition analytics"""
    return {}


def get_job_completion_metrics():
    """Get job completion rate analytics"""
    return {}


def get_provider_performance_metrics():
    """Get provider performance analytics"""
    return {}


def get_market_penetration_metrics():
    """Get market penetration analytics"""
    return {}


def get_growth_forecasting():
    """Get growth forecasting data"""
    return {}


def get_competitive_metrics():
    """Get competitive analysis metrics"""
    return {}
