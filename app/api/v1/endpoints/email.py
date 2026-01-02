from fastapi import APIRouter, HTTPException, Form

from app_logging.logger import get_logger
from app_logging.id_hasher import hash_email, hash_id  # PHI protection
from email_service.service import send_email
from email_service.tenant_mail import tenant_mail_template

logger = get_logger(__name__)
router = APIRouter()


@router.post("/send-creds")
async def send_credentials_endpoint(
    token: str = Form(...),
    identifier: str = Form(...),
    role: str = Form(...)
):
    """
    Sends login credentials to a user with a gratitude message and login instructions.
    The email is sent only to the user's email address (identifier).
    """
    subject = "Your Nurture Bridge Tech Account Credentials"
    
    # Determine login URL based on role
    if role.upper() == "PARENT":
        login_url = f"https://nb-v1.vercel.app/onboarding?token={token}"
    else:
        login_url = f"https://nbt-admin.vercel.app/onboarding?token={token}"
    
    body = tenant_mail_template.format(
        token=token,
        identifier=identifier,
        role=role,
        login_url=login_url
    )
    
    # Send email only to the user's identifier (email address)
    logger.info("sending_credentials_email", recipient_hash=hash_email(identifier), token_hash=hash_id(token))
    success = send_email(identifier, subject, body)
    
    if success:
        logger.info("credentials_email_sent", recipient_hash=hash_email(identifier), token_hash=hash_id(token))
        return {
            "status": "success", 
            "message": "Credentials email sent successfully."  # Removed email from message - PHI
        }
    else:
        logger.error("credentials_email_failed", recipient_hash=hash_email(identifier), token_hash=hash_id(token))
        raise HTTPException(
            status_code=500,
            detail="Failed to send credentials email. Please check the server logs for more details."
        )
