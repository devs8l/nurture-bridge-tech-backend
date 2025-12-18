import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import structlog

from config.settings import settings

logger = structlog.get_logger(__name__)

class EmailService:
    """
    Email service for sending transactional emails via SMTP.
    """
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_use_tls = settings.SMTP_USE_TLS
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text fallback (optional)
        
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add text part (fallback)
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)
            
            # Add HTML part
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                
                server.send_message(msg)
            
            logger.info(
                "email_sent",
                to_email=to_email,
                subject=subject
            )
            return True
            
        except Exception as e:
            logger.error(
                "email_send_failed",
                to_email=to_email,
                subject=subject,
                error=str(e)
            )
            return False
    
    async def send_invitation_email(
        self,
        to_email: str,
        token: str,
        role: str,
        tenant_name: Optional[str] = None
    ) -> bool:
        """
        Send invitation email with acceptance link.
        
        Args:
            to_email: Invitee email address
            token: Invitation token
            role: Role being invited to
            tenant_name: Organization name (optional)
        
        Returns:
            True if email sent successfully
        """
        # Build invitation link
        frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else "http://localhost:3000"
        invitation_link = f"{frontend_url}/accept-invitation?token={token}"
        
        # Format role name
        role_display = role.replace("_", " ").title()
        
        # Build HTML content
        html_content = self._build_invitation_html(
            to_email=to_email,
            role=role_display,
            invitation_link=invitation_link,
            tenant_name=tenant_name or "Nurture Bridge"
        )
        
        # Build plain text fallback
        text_content = f"""
You've been invited to join {tenant_name or 'Nurture Bridge'} as a {role_display}.

Click the link below to accept your invitation:
{invitation_link}

This invitation expires in 7 days.

If you didn't expect this invitation, you can safely ignore this email.
        """
        
        subject = f"You're invited to join {tenant_name or 'Nurture Bridge'}"
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    def _build_invitation_html(
        self,
        to_email: str,
        role: str,
        invitation_link: str,
        tenant_name: str
    ) -> str:
        """Build HTML content for invitation email."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }}
        .container {{
            max-width: 600px;
            margin: 40px auto;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }}
        .content {{
            padding: 40px 30px;
        }}
        .content p {{
            margin: 0 0 20px 0;
            font-size: 16px;
        }}
        .button {{
            display: inline-block;
            background: #667eea;
            color: white !important;
            text-decoration: none;
            padding: 14px 32px;
            border-radius: 6px;
            font-weight: 600;
            margin: 20px 0;
            transition: background 0.3s;
        }}
        .button:hover {{
            background: #5568d3;
        }}
        .info-box {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px 30px;
            text-align: center;
            font-size: 14px;
            color: #666;
        }}
        .footer a {{
            color: #667eea;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 You're Invited!</h1>
        </div>
        
        <div class="content">
            <p>Hello,</p>
            
            <p>You've been invited to join <strong>{tenant_name}</strong> as a <strong>{role}</strong>.</p>
            
            <p>Click the button below to accept your invitation and set up your account:</p>
            
            <center>
                <a href="{invitation_link}" class="button">Accept Invitation</a>
            </center>
            
            <div class="info-box">
                <strong>⏰ Important:</strong> This invitation expires in 7 days.
            </div>
            
            <p>If you didn't expect this invitation, you can safely ignore this email.</p>
        </div>
        
        <div class="footer">
            <p>© 2025 Nurture Bridge. All rights reserved.</p>
            <p>This is an automated email. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
        """
