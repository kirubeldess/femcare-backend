# utils/sms_helper.py
import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Attempt to load environment variables
load_dotenv()

# Get the logger
logger = logging.getLogger(__name__)

# Check if Twilio is configured
TWILIO_ENABLED = (
    os.getenv("TWILIO_ACCOUNT_SID") is not None
    and os.getenv("TWILIO_AUTH_TOKEN") is not None
)

# Only import Twilio if it's enabled
if TWILIO_ENABLED:
    try:
        from twilio.rest import Client

        twilio_client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN")
        )
        TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
    except ImportError:
        logger.warning(
            "Twilio package not installed. SMS functionality will be disabled."
        )
        TWILIO_ENABLED = False


async def send_emergency_sms(to: str, message: str) -> bool:
    """
    Send an emergency SMS using Twilio.

    Args:
        to (str): The phone number to send the SMS to
        message (str): The message content

    Returns:
        bool: True if the message was sent, False otherwise
    """
    # Log the attempt
    logger.info(f"Attempting to send emergency SMS to {to}")

    # Format the phone number if it doesn't have the + prefix
    if not to.startswith("+"):
        to = f"+{to}"

    # Check if Twilio is enabled
    if not TWILIO_ENABLED:
        logger.warning("Twilio is not configured. SMS not sent.")
        return False

    try:
        # Send the message
        twilio_client.messages.create(body=message, from_=TWILIO_PHONE_NUMBER, to=to)
        logger.info(f"Emergency SMS sent successfully to {to}")
        return True
    except Exception as e:
        logger.error(f"Failed to send emergency SMS: {str(e)}")
        return False


# Fallback method for environments without Twilio
def log_emergency_message(to: str, message: str) -> None:
    """
    Fallback function to log emergency messages when Twilio is not available
    """
    logger.warning(f"EMERGENCY MESSAGE (not sent via SMS):")
    logger.warning(f"To: {to}")
    logger.warning(f"Message: {message}")
