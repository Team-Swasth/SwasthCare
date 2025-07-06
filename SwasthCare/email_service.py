from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from azure.communication.email import EmailClient
from azure.identity import DefaultAzureCredential
import logging

logger = logging.getLogger(__name__)

class AzureCommunicationService:
    """Azure Communication Services for sending emails with Django fallback"""
    
    def __init__(self):
        """Initialize Azure Communication Services client with fallback to Django email"""
        self.use_azure = False
        self.email_client = None
        
        try:
            # Try to use Azure Communication Services first
            connection_string = getattr(settings, 'AZURE_COMMUNICATION_CONNECTION_STRING', None)
            
            if connection_string:
                self.email_client = EmailClient.from_connection_string(connection_string)
                self.use_azure = True
                logger.info("Using Azure Communication Services for email")
            else:
                # Fallback to managed identity (for production)
                credential = DefaultAzureCredential()
                endpoint = getattr(settings, 'AZURE_COMMUNICATION_ENDPOINT', None)
                if endpoint:
                    self.email_client = EmailClient(endpoint, credential)
                    self.use_azure = True
                    logger.info("Using Azure Communication Services with managed identity")
                else:
                    logger.info("No Azure Communication Services configuration found, using Django email backend")
                    
            self.from_email = getattr(settings, 'AZURE_COMMUNICATION_FROM_EMAIL', 
                                    getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@swasthcare.com'))
            
        except Exception as e:
            logger.warning(f"Failed to initialize Azure Communication Services: {e}. Falling back to Django email backend.")
            self.use_azure = False
            self.email_client = None
    
    def send_password_reset_email(self, user_email, reset_link, user_name=None):
        """Send password reset email using Azure or Django email backend"""
        
        if self.use_azure and self.email_client:
            return self._send_azure_email(user_email, reset_link, user_name)
        else:
            return self._send_django_email(user_email, reset_link, user_name)
    
    def _send_django_email(self, user_email, reset_link, user_name=None):
        """Send email using Django's email backend"""
        try:
            subject = "SwasthCare - Password Reset Request"
            
            # Create the email content
            message = f"""
Hello{f" {user_name}" if user_name else ""},

We received a request to reset your password for your SwasthCare account.

To reset your password, click the link below:
{reset_link}

Important: This link will expire in 24 hours for security reasons.

If you didn't make this request, you can safely ignore this email.

Best regards,
The SwasthCare Team

© 2025 SwasthCare. All rights reserved.
This is an automated message. Please do not reply to this email.
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@swasthcare.com'),
                recipient_list=[user_email],
                fail_silently=False,
            )
            
            logger.info(f"Password reset email sent successfully to {user_email} using Django email backend")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset email using Django backend: {e}")
            return False
    
    def _send_azure_email(self, user_email, reset_link, user_name=None):
        """Send password reset email using Azure Communication Services"""
        try:
            subject = "SwasthCare - Password Reset Request"
            
            # HTML email template
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Password Reset - SwasthCare</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f8f9fa; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; }}
                    .header {{ background: linear-gradient(135deg, #4CAF50, #388E3C); color: white; padding: 2rem; text-align: center; }}
                    .content {{ padding: 2rem; }}
                    .button {{ display: inline-block; background: #4CAF50; color: white; text-decoration: none; padding: 12px 30px; border-radius: 25px; margin: 1rem 0; }}
                    .footer {{ background-color: #f8f9fa; padding: 1rem; text-align: center; color: #6c757d; font-size: 0.9rem; }}
                    .logo {{ font-size: 1.5rem; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">🌿 SwasthCare</div>
                        <h1>Password Reset Request</h1>
                    </div>
                    <div class="content">
                        <p>Hello{f" {user_name}" if user_name else ""},</p>
                        
                        <p>We received a request to reset your password for your SwasthCare account. If you didn't make this request, you can safely ignore this email.</p>
                        
                        <p>To reset your password, click the button below:</p>
                        
                        <a href="{reset_link}" class="button">Reset Password</a>
                        
                        <p>Or copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; color: #4CAF50;">{reset_link}</p>
                        
                        <p><strong>Important:</strong> This link will expire in 24 hours for security reasons.</p>
                        
                        <p>If you're having trouble with the link, please contact our support team.</p>
                        
                        <p>Best regards,<br>The SwasthCare Team</p>
                    </div>
                    <div class="footer">
                        <p>© 2025 SwasthCare. All rights reserved.</p>
                        <p>This is an automated message. Please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_content = f"""
            SwasthCare - Password Reset Request
            
            Hello{f" {user_name}" if user_name else ""},
            
            We received a request to reset your password for your SwasthCare account.
            
            To reset your password, click or copy the following link:
            {reset_link}
            
            This link will expire in 24 hours for security reasons.
            
            If you didn't make this request, you can safely ignore this email.
            
            Best regards,
            The SwasthCare Team
            
            © 2025 SwasthCare. All rights reserved.
            """
            
            message = {
                "content": {
                    "subject": subject,
                    "plainText": text_content,
                    "html": html_content
                },
                "recipients": {
                    "to": [
                        {
                            "address": user_email,
                            "displayName": user_name or ""
                        }
                    ]
                },
                "senderAddress": self.from_email
            }
            
            # Send email
            response = self.email_client.begin_send(message)
            result = response.result()
            
            logger.info(f"Password reset email sent successfully to {user_email}. Message ID: {result.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user_email}: {e}")
            return False
    
    def send_welcome_email(self, user_email, user_name, is_seller=False):
        """Send welcome email to new users"""
        if not self.email_client:
            logger.error("Azure Communication Services not initialized")
            return False
            
        try:
            user_type = "Seller" if is_seller else "Consumer"
            subject = f"Welcome to SwasthCare - Your {user_type} Account is Ready!"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Welcome to SwasthCare</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f8f9fa; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; }}
                    .header {{ background: linear-gradient(135deg, #4CAF50, #388E3C); color: white; padding: 2rem; text-align: center; }}
                    .content {{ padding: 2rem; }}
                    .feature {{ background-color: #f8f9fa; padding: 1rem; margin: 1rem 0; border-radius: 8px; }}
                    .button {{ display: inline-block; background: #4CAF50; color: white; text-decoration: none; padding: 12px 30px; border-radius: 25px; margin: 1rem 0; }}
                    .footer {{ background-color: #f8f9fa; padding: 1rem; text-align: center; color: #6c757d; font-size: 0.9rem; }}
                    .logo {{ font-size: 1.5rem; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">🌿 SwasthCare</div>
                        <h1>Welcome to SwasthCare!</h1>
                    </div>
                    <div class="content">
                        <p>Hello {user_name},</p>
                        
                        <p>Welcome to SwasthCare! Your {user_type.lower()} account has been successfully created. We're excited to have you join our community focused on making informed food choices.</p>
                        
                        {"<div class='feature'><h3>🏪 As a Seller, you can:</h3><ul><li>Upload product images for AI analysis</li><li>Manage your product database</li><li>Provide detailed nutritional information</li><li>Help consumers make informed choices</li></ul></div>" if is_seller else "<div class='feature'><h3>🛍️ As a Consumer, you can:</h3><ul><li>Scan product barcodes</li><li>Get detailed nutritional information</li><li>Receive allergen alerts</li><li>Track your search history</li></ul></div>"}
                        
                        <p>Ready to get started?</p>
                        
                        <a href="http://127.0.0.1:8000/login/" class="button">Login to Your Account</a>
                        
                        <p>If you have any questions or need assistance, feel free to reach out to our support team.</p>
                        
                        <p>Best regards,<br>The SwasthCare Team</p>
                    </div>
                    <div class="footer">
                        <p>© 2025 SwasthCare. All rights reserved.</p>
                        <p>This is an automated message. Please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            message = {
                "content": {
                    "subject": subject,
                    "html": html_content
                },
                "recipients": {
                    "to": [
                        {
                            "address": user_email,
                            "displayName": user_name
                        }
                    ]
                },
                "senderAddress": self.from_email
            }
            
            response = self.email_client.begin_send(message)
            result = response.result()
            
            logger.info(f"Welcome email sent successfully to {user_email}. Message ID: {result.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user_email}: {e}")
            return False

# Global instance
azure_communication_service = AzureCommunicationService()
