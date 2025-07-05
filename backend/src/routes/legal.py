"""
Legal Routes
===========

Routes for serving legal documents and compliance pages.
"""

from flask import Blueprint, render_template

from src.utils.error_handling import handle_errors

# Create blueprint
legal_bp = Blueprint("legal", __name__)


@legal_bp.route("/privacy")
@handle_errors()
def privacy_policy():
    """Privacy Policy page"""
    return render_template("privacy.html")


@legal_bp.route("/terms")
@handle_errors()
def terms_of_service():
    """Terms of Service page"""
    return render_template("terms.html")


@legal_bp.route("/cookies")
@handle_errors()
def cookie_policy():
    """Cookie Policy page"""
    return render_template("cookies.html")


@legal_bp.route("/accessibility")
@handle_errors()
def accessibility_statement():
    """Accessibility Statement page"""
    return render_template("accessibility.html")


# Additional business information routes
@legal_bp.route("/contact")
@handle_errors()
def contact_info():
    """Contact information page"""
    # For now, redirect to main contact or create a simple contact page
    return render_template("contact.html")


@legal_bp.route("/about")
@handle_errors()
def about_us():
    """About Us page"""
    return render_template("about.html")
