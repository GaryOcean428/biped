import os
import requests
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailMicroserviceClient:
    """Client for communicating with external email microservice"""
    
    def __init__(self):
        self.email_service_url = os.getenv('EMAIL_SERVICE_URL', 'http://localhost:3001')
        self.email_service_api_key = os.getenv('EMAIL_SERVICE_API_KEY', '')
        self.timeout = int(os.getenv('EMAIL_SERVICE_TIMEOUT', '30'))
        
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to email microservice"""
        try:
            url = f"{self.email_service_url.rstrip('/')}/{endpoint.lstrip('/')}"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.email_service_api_key}' if self.email_service_api_key else ''
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            else:
                logger.error(f"Email service error: {response.status_code} - {response.text}")
                return {'success': False, 'error': f"HTTP {response.status_code}: {response.text}"}
                
        except requests.exceptions.Timeout:
            logger.error("Email service timeout")
            return {'success': False, 'error': 'Email service timeout'}
        except requests.exceptions.ConnectionError:
            logger.error("Email service connection error")
            return {'success': False, 'error': 'Email service unavailable'}
        except Exception as e:
            logger.error(f"Email service request error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def send_email(self, 
                   to_emails: List[str], 
                   subject: str, 
                   html_content: str, 
                   text_content: Optional[str] = None,
                   template_id: Optional[str] = None,
                   template_data: Optional[Dict] = None) -> bool:
        """Send email via microservice"""
        
        data = {
            'to': to_emails,
            'subject': subject,
            'html_content': html_content,
            'text_content': text_content,
            'template_id': template_id,
            'template_data': template_data or {},
            'from_email': os.getenv('FROM_EMAIL', 'noreply@biped.com'),
            'from_name': os.getenv('FROM_NAME', 'Biped Platform')
        }
        
        result = self._make_request('/api/send', data)
        return result['success']
    
    def send_template_email(self, 
                           to_emails: List[str], 
                           template_id: str, 
                           template_data: Dict[str, Any]) -> bool:
        """Send email using predefined template"""
        
        data = {
            'to': to_emails,
            'template_id': template_id,
            'template_data': template_data,
            'from_email': os.getenv('FROM_EMAIL', 'noreply@biped.com'),
            'from_name': os.getenv('FROM_NAME', 'Biped Platform')
        }
        
        result = self._make_request('/api/send-template', data)
        return result['success']
    
    def get_email_status(self, email_id: str) -> Dict[str, Any]:
        """Get email delivery status"""
        result = self._make_request('/api/status', {'email_id': email_id})
        return result.get('data', {}) if result['success'] else {}
    
    def test_connection(self) -> bool:
        """Test connection to email microservice"""
        result = self._make_request('/api/health', {})
        return result['success']

class EnhancedNotificationService:
    """Enhanced notification service with microservice integration"""
    
    def __init__(self):
        self.use_microservice = os.getenv('USE_EMAIL_MICROSERVICE', 'false').lower() == 'true'
        
        if self.use_microservice:
            self.email_client = EmailMicroserviceClient()
        else:
            # Fallback to local email service
            from src.services.communication import EmailService
            self.email_client = EmailService()
        
        # SMS service remains local for now
        from src.services.communication import SMSService
        self.sms_service = SMSService()
    
    def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Send welcome email to new users"""
        if self.use_microservice:
            return self.email_client.send_template_email(
                [user_email],
                'welcome',
                {
                    'user_name': user_name,
                    'user_email': user_email,
                    'dashboard_url': 'https://biped.com/dashboard'
                }
            )
        else:
            # Use local email service with full HTML content
            subject = "Welcome to Biped - Your Service Marketplace"
            html_content = self._get_welcome_email_html(user_name, user_email)
            text_content = self._get_welcome_email_text(user_name)
            
            return self.email_client.send_email([user_email], subject, html_content, text_content)
    
    def send_job_notification(self, provider_email: str, provider_name: str, job_title: str, job_id: str) -> bool:
        """Send job notification to service providers"""
        if self.use_microservice:
            return self.email_client.send_template_email(
                [provider_email],
                'job_notification',
                {
                    'provider_name': provider_name,
                    'job_title': job_title,
                    'job_id': job_id,
                    'job_url': f'https://biped.com/jobs/{job_id}'
                }
            )
        else:
            subject = f"New Job Opportunity: {job_title}"
            html_content = self._get_job_notification_html(provider_name, job_title, job_id)
            
            return self.email_client.send_email([provider_email], subject, html_content)
    
    def send_quote_notification(self, customer_email: str, customer_name: str, provider_name: str, job_title: str, quote_amount: float) -> bool:
        """Send quote notification to customers"""
        if self.use_microservice:
            return self.email_client.send_template_email(
                [customer_email],
                'quote_notification',
                {
                    'customer_name': customer_name,
                    'provider_name': provider_name,
                    'job_title': job_title,
                    'quote_amount': quote_amount,
                    'dashboard_url': 'https://biped.com/dashboard'
                }
            )
        else:
            subject = f"New Quote Received for: {job_title}"
            html_content = self._get_quote_notification_html(customer_name, provider_name, job_title, quote_amount)
            
            return self.email_client.send_email([customer_email], subject, html_content)
    
    def send_payment_confirmation_email(self, user_email: str, user_name: str, amount: float, job_title: str) -> bool:
        """Send payment confirmation email"""
        if self.use_microservice:
            return self.email_client.send_template_email(
                [user_email],
                'payment_confirmation',
                {
                    'user_name': user_name,
                    'amount': amount,
                    'job_title': job_title,
                    'date': datetime.now().strftime('%B %d, %Y')
                }
            )
        else:
            subject = "Payment Confirmation - Biped"
            html_content = self._get_payment_confirmation_html(user_name, amount, job_title)
            
            return self.email_client.send_email([user_email], subject, html_content)
    
    def send_sms_notification(self, phone_number: str, message: str) -> bool:
        """Send SMS notification"""
        return self.sms_service.send_sms(phone_number, message)
    
    def test_email_service(self) -> Dict[str, Any]:
        """Test email service connectivity"""
        if self.use_microservice:
            connected = self.email_client.test_connection()
            return {
                'service_type': 'microservice',
                'connected': connected,
                'url': self.email_client.email_service_url
            }
        else:
            return {
                'service_type': 'local',
                'connected': True,
                'provider': getattr(self.email_client, 'provider', 'unknown')
            }
    
    def _get_welcome_email_html(self, user_name: str, user_email: str) -> str:
        """Get welcome email HTML content"""
        return f"""
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
    
    def _get_welcome_email_text(self, user_name: str) -> str:
        """Get welcome email text content"""
        return f"""
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
    
    def _get_job_notification_html(self, provider_name: str, job_title: str, job_id: str) -> str:
        """Get job notification HTML content"""
        return f"""
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
    
    def _get_quote_notification_html(self, customer_name: str, provider_name: str, job_title: str, quote_amount: float) -> str:
        """Get quote notification HTML content"""
        return f"""
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
    
    def _get_payment_confirmation_html(self, user_name: str, amount: float, job_title: str) -> str:
        """Get payment confirmation HTML content"""
        return f"""
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

# Global enhanced notification service instance
enhanced_notification_service = EnhancedNotificationService()

