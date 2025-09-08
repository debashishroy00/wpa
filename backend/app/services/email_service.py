"""
WealthPath AI - Email Service
"""
import logging
from typing import List, Optional
from pydantic import EmailStr
from app.core.config import settings
import structlog

# Optional import for fastapi-mail
try:
    from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
    FASTAPI_MAIL_AVAILABLE = True
except ImportError:
    FASTAPI_MAIL_AVAILABLE = False
    FastMail = None
    MessageSchema = None
    ConnectionConfig = None
    MessageType = None

logger = structlog.get_logger()

# Configure email connection (only if fastapi-mail is available)
if FASTAPI_MAIL_AVAILABLE:
    conf = ConnectionConfig(
        MAIL_USERNAME=settings.SMTP_USERNAME,
        MAIL_PASSWORD=settings.SMTP_PASSWORD,
        MAIL_FROM=settings.SMTP_FROM_EMAIL,
        MAIL_PORT=settings.SMTP_PORT,
        MAIL_SERVER=settings.SMTP_SERVER,
        MAIL_STARTTLS=settings.SMTP_USE_TLS,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True
    )
    fastmail = FastMail(conf)
else:
    conf = None
    fastmail = None


class EmailService:
    """Email service for sending various types of emails"""
    
    async def send_password_reset_email(
        self, 
        email: str, 
        reset_token: str, 
        user_name: str = None
    ) -> bool:
        """
        Send password reset email with reset link
        """
        if not FASTAPI_MAIL_AVAILABLE:
            logger.warning(
                "FastAPI-Mail not available, logging reset token instead",
                email=email,
                token=reset_token
            )
            return True
            
        try:
            # Create reset link (this would be your frontend URL)
            reset_link = f"https://smartfinanceadvisor.net/#/reset-password?token={reset_token}"
            
            # Create HTML email template
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Password Reset - WealthPath AI</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #667eea; color: white; padding: 20px; text-align: center; }}
                    .content {{ background-color: #f9f9f9; padding: 30px; }}
                    .button {{ display: inline-block; background-color: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; }}
                    .footer {{ background-color: #f0f0f0; padding: 20px; font-size: 12px; text-align: center; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>WealthPath AI</h1>
                    </div>
                    <div class="content">
                        <h2>Password Reset Request</h2>
                        <p>Hello{f" {user_name}" if user_name else ""},</p>
                        <p>We received a request to reset your password for your WealthPath AI account.</p>
                        <p>Click the button below to reset your password:</p>
                        <p style="text-align: center; margin: 30px 0;">
                            <a href="{reset_link}" class="button">Reset Password</a>
                        </p>
                        <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; background-color: #e9e9e9; padding: 10px; font-family: monospace;">
                            {reset_link}
                        </p>
                        <p>This link will expire in 1 hour for security reasons.</p>
                        <p>If you didn't request this password reset, please ignore this email. Your password will remain unchanged.</p>
                        <p>Best regards,<br>The WealthPath AI Team</p>
                    </div>
                    <div class="footer">
                        <p>This is an automated message. Please do not reply to this email.</p>
                        <p>© 2024 WealthPath AI. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create plain text version
            text_content = f"""
            WealthPath AI - Password Reset Request
            
            Hello{f" {user_name}" if user_name else ""},
            
            We received a request to reset your password for your WealthPath AI account.
            
            Please click or copy the following link to reset your password:
            {reset_link}
            
            This link will expire in 1 hour for security reasons.
            
            If you didn't request this password reset, please ignore this email. Your password will remain unchanged.
            
            Best regards,
            The WealthPath AI Team
            
            ---
            This is an automated message. Please do not reply to this email.
            © 2024 WealthPath AI. All rights reserved.
            """
            
            # Create message
            message = MessageSchema(
                subject="Reset Your WealthPath AI Password",
                recipients=[email],
                body=text_content,
                html=html_content,
                subtype=MessageType.html
            )
            
            # Send email
            await fastmail.send_message(message)
            
            logger.info(
                "Password reset email sent successfully",
                email=email,
                user_name=user_name
            )
            return True
            
        except Exception as e:
            logger.error(
                "Failed to send password reset email",
                email=email,
                error=str(e)
            )
            return False
    
    async def send_welcome_email(
        self, 
        email: str, 
        user_name: str
    ) -> bool:
        """
        Send welcome email to new users
        """
        if not FASTAPI_MAIL_AVAILABLE:
            logger.warning(
                "FastAPI-Mail not available, skipping welcome email",
                email=email,
                user_name=user_name
            )
            return True
            
        try:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Welcome to WealthPath AI</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #667eea; color: white; padding: 20px; text-align: center; }}
                    .content {{ background-color: #f9f9f9; padding: 30px; }}
                    .button {{ display: inline-block; background-color: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; }}
                    .footer {{ background-color: #f0f0f0; padding: 20px; font-size: 12px; text-align: center; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to WealthPath AI!</h1>
                    </div>
                    <div class="content">
                        <h2>Hello {user_name}!</h2>
                        <p>Welcome to WealthPath AI - your intelligent financial planning platform.</p>
                        <p>We're excited to help you on your journey to financial success. Here's what you can do with WealthPath AI:</p>
                        <ul>
                            <li>Get personalized financial advice from our AI advisor</li>
                            <li>Track your financial goals and progress</li>
                            <li>Analyze your spending patterns and budget</li>
                            <li>Plan for retirement and major life events</li>
                        </ul>
                        <p style="text-align: center; margin: 30px 0;">
                            <a href="https://smartfinanceadvisor.net" class="button">Get Started</a>
                        </p>
                        <p>If you have any questions, feel free to reach out to our support team.</p>
                        <p>Best regards,<br>The WealthPath AI Team</p>
                    </div>
                    <div class="footer">
                        <p>© 2024 WealthPath AI. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            Welcome to WealthPath AI!
            
            Hello {user_name}!
            
            Welcome to WealthPath AI - your intelligent financial planning platform.
            
            We're excited to help you on your journey to financial success. Here's what you can do with WealthPath AI:
            
            • Get personalized financial advice from our AI advisor
            • Track your financial goals and progress  
            • Analyze your spending patterns and budget
            • Plan for retirement and major life events
            
            Visit us at: https://smartfinanceadvisor.net
            
            If you have any questions, feel free to reach out to our support team.
            
            Best regards,
            The WealthPath AI Team
            
            ---
            © 2024 WealthPath AI. All rights reserved.
            """
            
            message = MessageSchema(
                subject="Welcome to WealthPath AI - Let's Get Started!",
                recipients=[email],
                body=text_content,
                html=html_content,
                subtype=MessageType.html
            )
            
            await fastmail.send_message(message)
            
            logger.info(
                "Welcome email sent successfully",
                email=email,
                user_name=user_name
            )
            return True
            
        except Exception as e:
            logger.error(
                "Failed to send welcome email",
                email=email,
                error=str(e)
            )
            return False


# Global email service instance
email_service = EmailService()