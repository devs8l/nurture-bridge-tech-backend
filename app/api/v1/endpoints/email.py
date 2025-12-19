from fastapi import APIRouter, HTTPException, Form

from app_logging.logger import get_logger
from email_service.service import send_email
from email_service.tenant_mail import tenant_mail_template

logger = get_logger(__name__)
router = APIRouter()


@router.post("/send-creds")
async def send_credentials_endpoint(
    tenant_id: str = Form(...),
    identifier: str = Form(...),
    password: str = Form(...)
):
    """
    Sends login credentials to a user with a gratitude message and login instructions.
    The email is sent only to the user's email address (identifier).
    """
    subject = "Your Nurture Bridge Tech Account Credentials"
    
    body = tenant_mail_template.format(
        tenant_id=tenant_id,
        identifier=identifier,
        password=password
    )
    
    # Send email only to the user's identifier (email address)
    logger.info("sending_credentials_email", recipient=identifier, tenant_id=tenant_id)
    success = send_email(identifier, subject, body)
    
    if success:
        logger.info("credentials_email_sent", recipient=identifier, tenant_id=tenant_id)
        return {
            "status": "success", 
            "message": f"Credentials email sent successfully to {identifier}."
        }
    else:
        logger.error("credentials_email_failed", recipient=identifier, tenant_id=tenant_id)
        raise HTTPException(
            status_code=500,
            detail="Failed to send credentials email. Please check the server logs for more details."
        )
