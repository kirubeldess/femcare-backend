import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.sender_email = os.getenv("SENDER_EMAIL", "femcare.noreply@example.com")
        self.sender_password = os.getenv("SENDER_PASSWORD", "your_password")

    def send_appointment_confirmation(
        self, user_email, user_name, consultant_name, appointment_time
    ):
        """Send an appointment confirmation email to the user."""
        subject = "Your Appointment Confirmation"

        # Format the appointment time for better readability
        formatted_time = appointment_time.strftime("%A, %B %d, %Y at %I:%M %p")

        body = f"""
        <html>
        <body>
            <h2>Appointment Confirmation</h2>
            <p>Hello {user_name},</p>
            <p>Your appointment with {consultant_name} has been confirmed for:</p>
            <p><strong>{formatted_time}</strong></p>
            <p>If you need to reschedule or cancel, please log into your account.</p>
            <p>Thank you for using our services!</p>
            <p>Best regards,<br>FemCare Team</p>
        </body>
        </html>
        """

        return self._send_email(user_email, subject, body)

    def send_appointment_reminder(
        self, user_email, user_name, consultant_name, appointment_time
    ):
        """Send a reminder email about an upcoming appointment."""
        subject = "Reminder: Upcoming Appointment"

        # Format the appointment time for better readability
        formatted_time = appointment_time.strftime("%A, %B %d, %Y at %I:%M %p")

        body = f"""
        <html>
        <body>
            <h2>Appointment Reminder</h2>
            <p>Hello {user_name},</p>
            <p>This is a friendly reminder that you have an appointment scheduled with {consultant_name} for:</p>
            <p><strong>{formatted_time}</strong></p>
            <p>If you need to reschedule or cancel, please log into your account as soon as possible.</p>
            <p>Thank you for using our services!</p>
            <p>Best regards,<br>FemCare Team</p>
        </body>
        </html>
        """

        return self._send_email(user_email, subject, body)

    def send_consultant_invitation(self, email, signup_link, invited_by=None):
        """Send an invitation email to a potential consultant."""
        subject = "You're invited to join FemCare as a Consultant"

        inviter_info = (
            f"You have been invited by {invited_by}"
            if invited_by
            else "You have been invited"
        )

        body = f"""
        <html>
        <body>
            <h2>Consultant Invitation</h2>
            <p>Hello,</p>
            <p>{inviter_info} to join FemCare as a consultant. We value your expertise and would love to have you on our team.</p>
            <p>Please click the link below to complete your registration:</p>
            <p><a href="{signup_link}">{signup_link}</a></p>
            <p>This link will automatically assign you the consultant role in our system.</p>
            <p>If you did not expect this email, you can safely ignore it.</p>
            <p>Best regards,<br>FemCare Team</p>
        </body>
        </html>
        """

        return self._send_email(email, subject, body)

    def _send_email(self, recipient_email, subject, body):
        """Private method to handle the actual email sending."""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = recipient_email

            # Attach HTML part
            html_part = MIMEText(body, "html")
            message.attach(html_part)

            # Connect to the SMTP server
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient_email, message.as_string())

            logger.info(f"Email sent successfully to {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            return False


email_service = EmailService()
