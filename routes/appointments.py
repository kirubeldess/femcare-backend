import uuid
from typing import List, Optional, Dict
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from database import get_db
from models.appointment import Appointment, AppointmentStatus
from models.consultant_availability import ConsultantAvailability
from models.user import User
from models.consultant import Consultant
from pydantic_schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AvailabilityCreate,
    AvailabilityResponse,
    AvailabilitySlot,
)
from utils.auth import get_current_user
from services.email_service import email_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# CONSULTANT AVAILABILITY MANAGEMENT


@router.post(
    "/availability",
    response_model=AvailabilityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_availability_slot(
    availability: AvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new availability slot for a consultant. Only consultants or admins can create slots."""
    # Check if the user is an admin or the consultant themselves
    is_admin = current_user.role == "admin"
    is_consultant = (
        db.query(Consultant)
        .filter(
            Consultant.id == availability.consultant_id,
            Consultant.email == current_user.email,
        )
        .first()
        is not None
    )

    if not (is_admin or is_consultant):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only consultants can create their own availability slots or admins can create for any consultant.",
        )

    # Validate the time range
    if availability.start_time >= availability.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time.",
        )

    # Check for overlapping slots for the same consultant
    overlapping_slots = (
        db.query(ConsultantAvailability)
        .filter(
            ConsultantAvailability.consultant_id == availability.consultant_id,
            or_(
                and_(
                    ConsultantAvailability.start_time <= availability.start_time,
                    ConsultantAvailability.end_time > availability.start_time,
                ),
                and_(
                    ConsultantAvailability.start_time < availability.end_time,
                    ConsultantAvailability.end_time >= availability.end_time,
                ),
                and_(
                    ConsultantAvailability.start_time >= availability.start_time,
                    ConsultantAvailability.end_time <= availability.end_time,
                ),
            ),
        )
        .first()
    )

    if overlapping_slots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The time slot overlaps with an existing availability slot.",
        )

    # Create the availability slot
    db_availability = ConsultantAvailability(
        id=str(uuid.uuid4()),
        consultant_id=availability.consultant_id,
        start_time=availability.start_time,
        end_time=availability.end_time,
        is_booked=False,
    )

    try:
        db.add(db_availability)
        db.commit()
        db.refresh(db_availability)
        return db_availability
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating availability slot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create availability slot: {str(e)}",
        )


@router.get("/availability/consultant/{consultant_id}")
async def get_consultant_availability(
    consultant_id: str,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all available slots for a specific consultant, grouped by date."""
    # Check if the consultant exists
    consultant = db.query(Consultant).filter(Consultant.id == consultant_id).first()
    if not consultant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Consultant not found"
        )

    # Build the query
    query = db.query(ConsultantAvailability).filter(
        ConsultantAvailability.consultant_id == consultant_id,
        ConsultantAvailability.is_booked == False,
    )

    # Apply date filters if provided
    if from_date:
        query = query.filter(ConsultantAvailability.start_time >= from_date)

    if to_date:
        query = query.filter(ConsultantAvailability.end_time <= to_date)

    # Order by start time
    availability_slots = query.order_by(ConsultantAvailability.start_time).all()

    # Group by date using the new method
    result = ConsultantAvailability.group_by_date(availability_slots)

    if not result:
        result = {"consultant_id": consultant_id, "dates": {}}

    # Add consultant information
    result["name"] = consultant.name
    result["specialty"] = consultant.specialty

    return result


# APPOINTMENT MANAGEMENT


@router.post(
    "/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED
)
async def create_appointment(
    appointment: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Book an appointment in an available slot."""
    # Validate the time range
    if appointment.start_time >= appointment.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time.",
        )

    # Find the availability slot matching the requested time
    availability_slot = (
        db.query(ConsultantAvailability)
        .filter(
            ConsultantAvailability.consultant_id == appointment.consultant_id,
            ConsultantAvailability.start_time == appointment.start_time,
            ConsultantAvailability.end_time == appointment.end_time,
            ConsultantAvailability.is_booked == False,
        )
        .first()
    )

    if not availability_slot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The requested time slot is not available.",
        )

    # Get consultant info
    consultant = (
        db.query(Consultant).filter(Consultant.id == appointment.consultant_id).first()
    )
    if not consultant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Consultant not found"
        )

    # Create the appointment
    db_appointment = Appointment(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        consultant_id=appointment.consultant_id,
        start_time=appointment.start_time,
        end_time=appointment.end_time,
        status=AppointmentStatus.confirmed.value,
        notes=appointment.notes,
        reminder_sent=False,
    )

    try:
        # Mark the availability slot as booked
        availability_slot.is_booked = True

        # Add the appointment
        db.add(db_appointment)
        db.commit()
        db.refresh(db_appointment)

        # Send confirmation email
        try:
            email_service.send_appointment_confirmation(
                user_email=current_user.email,
                user_name=current_user.name,
                consultant_name=consultant.name,
                appointment_time=db_appointment.start_time,
            )
        except Exception as e:
            logger.error(f"Failed to send confirmation email: {str(e)}")

        return db_appointment
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating appointment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create appointment: {str(e)}",
        )


@router.get("/", response_model=List[AppointmentResponse])
async def get_user_appointments(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all appointments for the current user."""
    query = db.query(Appointment).filter(Appointment.user_id == current_user.id)

    if status:
        query = query.filter(Appointment.status == status)

    appointments = query.order_by(Appointment.start_time).all()
    return appointments


@router.get("/consultant/{consultant_id}", response_model=List[AppointmentResponse])
async def get_consultant_appointments(
    consultant_id: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all appointments for a specific consultant. Only for consultants or admins."""
    # Check permissions
    is_admin = current_user.role == "admin"
    is_consultant = (
        db.query(Consultant)
        .filter(Consultant.id == consultant_id, Consultant.email == current_user.email)
        .first()
        is not None
    )

    if not (is_admin or is_consultant):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only consultants can view their own appointments or admins can view any consultant's appointments.",
        )

    query = db.query(Appointment).filter(Appointment.consultant_id == consultant_id)

    if status:
        query = query.filter(Appointment.status == status)

    appointments = query.order_by(Appointment.start_time).all()
    return appointments


@router.put("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel an appointment."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found"
        )

    # Check if the user is the appointment owner or admin
    is_owner = appointment.user_id == current_user.id
    is_admin = current_user.role == "admin"
    is_consultant = (
        db.query(Consultant)
        .filter(
            Consultant.id == appointment.consultant_id,
            Consultant.email == current_user.email,
        )
        .first()
        is not None
    )

    if not (is_owner or is_admin or is_consultant):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to cancel this appointment",
        )

    # Check if the appointment is not already cancelled
    if appointment.status == AppointmentStatus.cancelled.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This appointment is already cancelled",
        )

    try:
        # Free up the availability slot
        availability_slot = (
            db.query(ConsultantAvailability)
            .filter(
                ConsultantAvailability.consultant_id == appointment.consultant_id,
                ConsultantAvailability.start_time == appointment.start_time,
                ConsultantAvailability.end_time == appointment.end_time,
            )
            .first()
        )

        if availability_slot:
            availability_slot.is_booked = False

        # Update appointment status
        appointment.status = AppointmentStatus.cancelled.value
        db.commit()
        db.refresh(appointment)

        return appointment
    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling appointment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel appointment: {str(e)}",
        )


@router.get("/send-reminders")
async def send_appointment_reminders(
    hours_before: int = 24,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send reminders for upcoming appointments. Only admins can trigger this manually."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can manually trigger reminders",
        )

    # Calculate the time window for sending reminders
    current_time = datetime.utcnow()
    reminder_time = current_time + timedelta(hours=hours_before)

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
        except Exception as e:
            logger.error(
                f"Error sending reminder for appointment {appointment.id}: {str(e)}"
            )

    db.commit()
    return {"message": f"Sent {sent_count} reminders for upcoming appointments"}
