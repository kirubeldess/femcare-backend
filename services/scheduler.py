import logging
import threading
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import get_db
from models.appointment import Appointment, AppointmentStatus
from models.user import User
from models.consultant import Consultant
from services.email_service import email_service

logger = logging.getLogger(__name__)


class AppointmentReminderScheduler:
    def __init__(self, reminder_hours_before=24, check_interval_seconds=3600):
        """
        Initialize the appointment reminder scheduler.

        Args:
            reminder_hours_before: How many hours before the appointment to send the reminder
            check_interval_seconds: How often to check for appointments needing reminders (default: 1 hour)
        """
        self.reminder_hours_before = reminder_hours_before
        self.check_interval_seconds = check_interval_seconds
        self.is_running = False
        self.scheduler_thread = None

    def start(self):
        """Start the scheduler in a background thread."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        self.is_running = True
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop, daemon=True
        )
        self.scheduler_thread.start()
        logger.info("Appointment reminder scheduler started")

    def stop(self):
        """Stop the scheduler."""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        logger.info("Appointment reminder scheduler stopped")

    def _scheduler_loop(self):
        """The main scheduler loop that runs in the background."""
        while self.is_running:
            try:
                self._send_reminders()
            except Exception as e:
                logger.error(f"Error in reminder scheduler: {str(e)}")

            # Sleep until the next check
            time.sleep(self.check_interval_seconds)

    def _send_reminders(self):
        """Send reminders for upcoming appointments."""
        logger.info("Checking for appointments requiring reminders...")

        # Get a new database session
        db = next(get_db())
        try:
            # Calculate the time window for sending reminders
            current_time = datetime.utcnow()
            reminder_time = current_time + timedelta(hours=self.reminder_hours_before)

            # Find upcoming appointments that haven't had reminders sent
            upcoming_appointments = (
                db.query(Appointment)
                .filter(
                    Appointment.status == AppointmentStatus.confirmed.value,
                    Appointment.reminder_sent == False,
                    Appointment.start_time <= reminder_time,
                    Appointment.start_time > current_time,
                )
                .all()
            )

            if not upcoming_appointments:
                logger.info("No appointments require reminders at this time")
                return

            logger.info(
                f"Found {len(upcoming_appointments)} appointments requiring reminders"
            )

            sent_count = 0
            for appointment in upcoming_appointments:
                try:
                    # Get user and consultant info
                    user = db.query(User).filter(User.id == appointment.user_id).first()
                    consultant = (
                        db.query(Consultant)
                        .filter(Consultant.id == appointment.consultant_id)
                        .first()
                    )

                    if user and consultant:
                        # Send the reminder email
                        email_sent = email_service.send_appointment_reminder(
                            user_email=user.email,
                            user_name=user.name,
                            consultant_name=consultant.name,
                            appointment_time=appointment.start_time,
                        )

                        if email_sent:
                            appointment.reminder_sent = True
                            sent_count += 1
                            logger.info(
                                f"Sent reminder for appointment {appointment.id} to {user.email}"
                            )
                        else:
                            logger.warning(
                                f"Failed to send reminder email for appointment {appointment.id}"
                            )
                except Exception as e:
                    logger.error(
                        f"Error sending reminder for appointment {appointment.id}: {str(e)}"
                    )

            db.commit()
            logger.info(f"Sent {sent_count} reminders for upcoming appointments")

        except Exception as e:
            db.rollback()
            logger.error(f"Error processing appointment reminders: {str(e)}")
        finally:
            db.close()


# Create a singleton instance
reminder_scheduler = AppointmentReminderScheduler()
