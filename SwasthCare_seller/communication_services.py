"""
Azure Communication Services integration for email functionality.
"""
import os
from django.conf import settings
import secrets
import string
import logging

logger = logging.getLogger(__name__)

# Try to import Azure Communication Services
try:
    from azure.communication.email import EmailClient
    from azure.core.credentials import AzureKeyCredential
    AZURE_COMMUNICATION_AVAILABLE = True
except ImportError:
    AZURE_COMMUNICATION_AVAILABLE = False
    logger.warning("Azure Communication Services not available. Email functionality will be disabled.")

class CommunicationService:
    """
    Azure Communication Services wrapper for email functionality.
    """
    
    def __init__(self):
        if not AZURE_COMMUNICATION_AVAILABLE:
            self.connection_string = None
            self.from_email = None
            self.email_client = None
            return
            
        self.connection_string = getattr(settings, 'AZURE_COMMUNICATION_CONNECTION_STRING', None)
        self.from_email = getattr(settings, 'AZURE_COMMUNICATION_FROM_EMAIL', 'donotreply@swasthcare.com')
        
        if not self.connection_string:
            logger.warning("Azure Communication Services connection string is not configured")
            self.email_client = None
            return
            
        try:
            self.email_client = EmailClient.from_connection_string(self.connection_string)
        except Exception as e:
            logger.error(f"Failed to initialize Azure Communication Services: {e}")
            self.email_client = None
    
    def generate_password(self, length=12):
        """Generate a secure random password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    def send_welcome_email(self, recipient_email, username, password, created_by=None):
        """
        Send welcome email to newly created seller account.
        
        Args:
            recipient_email (str): Email address of the new seller
            username (str): Username of the new seller
            password (str): Generated password
            created_by (str): Username of the seller who created this account
        """
        if not AZURE_COMMUNICATION_AVAILABLE or not self.email_client:
            logger.warning(f"Cannot send welcome email to {recipient_email}: Azure Communication Services not available")
            return False, "Email service not available"
            
        try:
            subject = "Welcome to SwasthCare - Your Seller Account"
            
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <h1 style="color: #4CAF50; margin: 0;">SwasthCare</h1>
                            <p style="color: #757575; margin: 5px 0;">Food Safety & Nutrition Platform</p>
                        </div>
                        
                        <h2 style="color: #333; margin-bottom: 20px;">Welcome to SwasthCare!</h2>
                        
                        <p style="color: #555; line-height: 1.6;">
                            Your seller account has been successfully created{' by ' + created_by if created_by else ''}. 
                            You can now start uploading and managing food products on our platform.
                        </p>
                        
                        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="color: #333; margin-top: 0;">Your Login Credentials:</h3>
                            <p style="margin: 10px 0;"><strong>Username:</strong> {username}</p>
                            <p style="margin: 10px 0;"><strong>Password:</strong> {password}</p>
                        </div>
                        
                        <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; margin: 20px 0;">
                            <p style="margin: 0; color: #856404;">
                                <strong>Important:</strong> Please change your password after your first login for security reasons.
                            </p>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="http://localhost:8000/login/" 
                               style="background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                                Login to SwasthCare
                            </a>
                        </div>
                        
                        <p style="color: #555; line-height: 1.6;">
                            If you have any questions or need assistance, please don't hesitate to contact our support team.
                        </p>
                        
                        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                        
                        <p style="color: #999; font-size: 12px; text-align: center;">
                            This email was sent automatically. Please do not reply to this email.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            text_content = f"""
            Welcome to SwasthCare!
            
            Your seller account has been successfully created{' by ' + created_by if created_by else ''}. 
            You can now start uploading and managing food products on our platform.
            
            Your Login Credentials:
            Username: {username}
            Password: {password}
            
            IMPORTANT: Please change your password after your first login for security reasons.
            
            Login at: http://localhost:8000/login/
            
            If you have any questions or need assistance, please don't hesitate to contact our support team.
            """
            
            message = {
                "senderAddress": self.from_email,
                "recipients": {
                    "to": [{"address": recipient_email}]
                },
                "content": {
                    "subject": subject,
                    "plainText": text_content,
                    "html": html_content
                }
            }
            
            poller = self.email_client.begin_send(message)
            result = poller.result()
            
            logger.info(f"Email sent successfully to {recipient_email}. Message ID: {result.message_id}")
            return True, result.message_id
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {recipient_email}: {str(e)}")
            return False, str(e)
    
    def send_password_reset_email(self, recipient_email, username, new_password):
        """
        Send password reset email.
        
        Args:
            recipient_email (str): Email address of the user
            username (str): Username of the user
            new_password (str): New generated password
        """
        if not AZURE_COMMUNICATION_AVAILABLE or not self.email_client:
            logger.warning(f"Cannot send password reset email to {recipient_email}: Azure Communication Services not available")
            return False, "Email service not available"
            
        try:
            subject = "SwasthCare - Password Reset"
            
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <h1 style="color: #4CAF50; margin: 0;">SwasthCare</h1>
                            <p style="color: #757575; margin: 5px 0;">Food Safety & Nutrition Platform</p>
                        </div>
                        
                        <h2 style="color: #333; margin-bottom: 20px;">Password Reset</h2>
                        
                        <p style="color: #555; line-height: 1.6;">
                            Your password has been reset as requested. Here are your new login credentials:
                        </p>
                        
                        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="color: #333; margin-top: 0;">Your New Login Credentials:</h3>
                            <p style="margin: 10px 0;"><strong>Username:</strong> {username}</p>
                            <p style="margin: 10px 0;"><strong>New Password:</strong> {new_password}</p>
                        </div>
                        
                        <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; margin: 20px 0;">
                            <p style="margin: 0; color: #856404;">
                                <strong>Important:</strong> Please change your password after logging in for security reasons.
                            </p>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="http://localhost:8000/login/" 
                               style="background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                                Login to SwasthCare
                            </a>
                        </div>
                        
                        <p style="color: #555; line-height: 1.6;">
                            If you didn't request this password reset, please contact our support team immediately.
                        </p>
                        
                        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                        
                        <p style="color: #999; font-size: 12px; text-align: center;">
                            This email was sent automatically. Please do not reply to this email.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            text_content = f"""
            SwasthCare - Password Reset
            
            Your password has been reset as requested. Here are your new login credentials:
            
            Username: {username}
            New Password: {new_password}
            
            IMPORTANT: Please change your password after logging in for security reasons.
            
            Login at: http://localhost:8000/login/
            
            If you didn't request this password reset, please contact our support team immediately.
            """
            
            message = {
                "senderAddress": self.from_email,
                "recipients": {
                    "to": [{"address": recipient_email}]
                },
                "content": {
                    "subject": subject,
                    "plainText": text_content,
                    "html": html_content
                }
            }
            
            poller = self.email_client.begin_send(message)
            result = poller.result()
            
            logger.info(f"Password reset email sent successfully to {recipient_email}. Message ID: {result.message_id}")
            return True, result.message_id
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {recipient_email}: {str(e)}")
            return False, str(e)


# Global instance
try:
    communication_service = CommunicationService()
except Exception as e:
    logger.error(f"Failed to initialize communication service: {e}")
    communication_service = None
