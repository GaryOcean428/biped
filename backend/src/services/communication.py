import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailService:
    """Email service supporting multiple providers"""
    
    def __init__(self):
        self.provider = os.getenv('EMAIL_PROVIDER', 'sendgrid')  # sendgrid, smtp, ses
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@biped.com')
        self.from_name = os.getenv('FROM_NAME', 'Biped Platform')
        
    def send_email(self, 
                   to_emails: List[str], 
                   subject: str, 
                   html_content: str, 
                   text_content: Optional[str] = None,
                   attachments: Optional[List[Dict]] = None) -> bool:
        """Send email using configured provider"""
        try:
            if self.provider == 'sendgrid':
                return self._send_sendgrid(to_emails, subject, html_content, text_content, attachments)
            elif self.provider == 'smtp':
                return self._send_smtp(to_emails, subject, html_content, text_content, attachments)
            else:
                logger.error(f"Unsupported email provider: {self.provider}")
                return False
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return False
    
    def _send_sendgrid(self, to_emails: List[str], subject: str, html_content: str, 
                       text_content: Optional[str] = None, attachments: Optional[List[Dict]] = None) -> bool:
        """Send email via SendGrid API"""
        if not self.sendgrid_api_key:
            logger.error("SendGrid API key not configured")
            return False
        
        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {self.sendgrid_api_key}",
            "Content-Type": "application/json"
        }
        
        personalizations = []
        for email in to_emails:
            personalizations.append({"to": [{"email": email}]})
        
        data = {
            "personalizations": personalizations,
            "from": {"email": self.from_email, "name": self.from_name},
            "subject": subject,
            "content": [
                {"type": "text/html", "value": html_content}
            ]
        }
        
        if text_content:
            data["content"].append({"type": "text/plain", "value": text_content})
        
        if attachments:
            data["attachments"] = attachments
        
        response = requests.post(url, json=data, headers=headers)
        return response.status_code == 202
    
    def _send_smtp(self, to_emails: List[str], subject: str, html_content: str, 
                   text_content: Optional[str] = None, attachments: Optional[List[Dict]] = None) -> bool:
        """Send email via SMTP"""
        if not self.smtp_username or not self.smtp_password:
            logger.error("SMTP credentials not configured")
            return False
        
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{self.from_name} <{self.from_email}>"
        msg['To'] = ", ".join(to_emails)
        msg['Subject'] = subject
        
        if text_content:
            msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        if attachments:
            for attachment in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment['content'])
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment["filename"]}'
                )
                msg.attach(part)
        
        server = smtplib.SMTP(self.smtp_host, self.smtp_port)
        server.starttls()
        server.login(self.smtp_username, self.smtp_password)
        server.send_message(msg)
        server.quit()
        return True

class SMSService:
    """SMS service supporting multiple providers"""
    
    def __init__(self):
        self.provider = os.getenv('SMS_PROVIDER', 'twilio')  # twilio, aws_sns
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
    def send_sms(self, to_phone: str, message: str) -> bool:
        """Send SMS using configured provider"""
        try:
            if self.provider == 'twilio':
                return self._send_twilio(to_phone, message)
            else:
                logger.error(f"Unsupported SMS provider: {self.provider}")
                return False
        except Exception as e:
            logger.error(f"SMS sending failed: {str(e)}")
            return False
    
    def _send_twilio(self, to_phone: str, message: str) -> bool:
        """Send SMS via Twilio API"""
        if not self.twilio_account_sid or not self.twilio_auth_token or not self.twilio_phone_number:
            logger.error("Twilio credentials not configured")
            return False
        
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"
        
        data = {
            'From': self.twilio_phone_number,
            'To': to_phone,
            'Body': message
        }
        
        response = requests.post(
            url,
            data=data,
            auth=(self.twilio_account_sid, self.twilio_auth_token)
        )
        
        return response.status_code == 201

class NotificationService:
    """Unified notification service for email and SMS"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.sms_service = SMSService()
        
    def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Send welcome email to new users"""
        subject = "Welcome to Biped - Your Service Marketplace"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #2563eb;">Welcome to Biped!</h1>
                </div>
                
                <p>Hi {user_name},</p>
                
                <p>Welcome to Biped, the premier marketplace connecting customers with skilled service providers!</p>
                
                <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #2563eb; margin-top: 0;">What you can do on Biped:</h3>
                    <ul>
                        <li>Post jobs and get quotes from qualified professionals</li>
                        <li>Browse and hire from our network of verified service providers</li>
                        <li>Manage projects with built-in communication tools</li>
                        <li>Make secure payments with our escrow system</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://biped.com/dashboard" 
                       style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Get Started
                    </a>
                </div>
                
                <p>If you have any questions, our support team is here to help!</p>
                
                <p>Best regards,<br>The Biped Team</p>
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                <p style="font-size: 12px; color: #6b7280; text-align: center;">
                    This email was sent to {user_email}. If you didn't create an account, please ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to Biped!
        
        Hi {user_name},
        
        Welcome to Biped, the premier marketplace connecting customers with skilled service providers!
        
        What you can do on Biped:
        - Post jobs and get quotes from qualified professionals
        - Browse and hire from our network of verified service providers
        - Manage projects with built-in communication tools
        - Make secure payments with our escrow system
        
        Get started: https://biped.com/dashboard
        
        If you have any questions, our support team is here to help!
        
        Best regards,
        The Biped Team
        """
        
        return self.email_service.send_email([user_email], subject, html_content, text_content)
    
    def send_job_notification(self, provider_email: str, provider_name: str, job_title: str, job_id: str) -> bool:
        """Send job notification to service providers"""
        subject = f"New Job Opportunity: {job_title}"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">New Job Opportunity</h2>
                
                <p>Hi {provider_name},</p>
                
                <p>A new job has been posted that matches your skills:</p>
                
                <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #2563eb; margin-top: 0;">{job_title}</h3>
                    <p><strong>Job ID:</strong> {job_id}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://biped.com/jobs/{job_id}" 
                       style="background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        View Job & Submit Quote
                    </a>
                </div>
                
                <p>Don't miss out on this opportunity!</p>
                
                <p>Best regards,<br>The Biped Team</p>
            </div>
        </body>
        </html>
        """
        
        return self.email_service.send_email([provider_email], subject, html_content)
    
    def send_quote_notification(self, customer_email: str, customer_name: str, provider_name: str, job_title: str, quote_amount: float) -> bool:
        """Send quote notification to customers"""
        subject = f"New Quote Received for: {job_title}"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">New Quote Received</h2>
                
                <p>Hi {customer_name},</p>
                
                <p>You've received a new quote for your job:</p>
                
                <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #2563eb; margin-top: 0;">{job_title}</h3>
                    <p><strong>Provider:</strong> {provider_name}</p>
                    <p><strong>Quote Amount:</strong> ${quote_amount:,.2f}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://biped.com/dashboard" 
                       style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Review Quote
                    </a>
                </div>
                
                <p>Review the quote and provider profile to make your decision.</p>
                
                <p>Best regards,<br>The Biped Team</p>
            </div>
        </body>
        </html>
        """
        
        return self.email_service.send_email([customer_email], subject, html_content)
    
    def send_sms_notification(self, phone_number: str, message: str) -> bool:
        """Send SMS notification"""
        return self.sms_service.send_sms(phone_number, message)
    
    def send_job_completion_sms(self, customer_phone: str, job_title: str) -> bool:
        """Send job completion SMS to customer"""
        message = f"Your job '{job_title}' has been completed! Please review and rate the service provider. - Biped"
        return self.send_sms_notification(customer_phone, message)
    
    def send_payment_confirmation_email(self, user_email: str, user_name: str, amount: float, job_title: str) -> bool:
        """Send payment confirmation email"""
        subject = "Payment Confirmation - Biped"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Payment Confirmation</h2>
                
                <p>Hi {user_name},</p>
                
                <p>Your payment has been processed successfully:</p>
                
                <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Job:</strong> {job_title}</p>
                    <p><strong>Amount:</strong> ${amount:,.2f}</p>
                    <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
                </div>
                
                <p>Thank you for using Biped!</p>
                
                <p>Best regards,<br>The Biped Team</p>
            </div>
        </body>
        </html>
        """
        
        return self.email_service.send_email([user_email], subject, html_content)

# Global notification service instance
notification_service = NotificationService()

