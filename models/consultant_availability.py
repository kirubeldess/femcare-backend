from models.base import Base
from sqlalchemy import Column, TEXT, TIMESTAMP, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship
from datetime import datetime
import json


class ConsultantAvailability(Base):
    __tablename__ = "consultant_availabilities"

    id = Column(TEXT, primary_key=True)
    consultant_id = Column(TEXT, ForeignKey("consultants.id"), nullable=False)
    start_time = Column(TIMESTAMP, nullable=False)
    end_time = Column(TIMESTAMP, nullable=False)
    is_booked = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Add relationship to consultant
    consultant = relationship("Consultant", backref="availabilities")

    @staticmethod
    def group_by_date(availabilities):
        """
        Group availability slots by date for a consultant

        Args:
            availabilities: List of ConsultantAvailability objects

        Returns:
            Dictionary in format {consultant_id: str, dates: {date_str: [slots]}}
        """
        if not availabilities:
            return None

        # Get consultant ID from first availability
        consultant_id = availabilities[0].consultant_id

        # Initialize result
        result = {"consultant_id": consultant_id, "dates": {}}

        # Group by date
        for avail in availabilities:
            # Get date as string (YYYY-MM-DD)
            date_str = avail.start_time.strftime("%Y-%m-%d")

            # Create date entry if it doesn't exist
            if date_str not in result["dates"]:
                result["dates"][date_str] = []

            # Add slot to date
            slot = {
                "id": avail.id,
                "start_time": avail.start_time.isoformat(),
                "end_time": avail.end_time.isoformat(),
                "is_booked": avail.is_booked,
            }

            result["dates"][date_str].append(slot)

        return result

    @classmethod
    def get_consultant_availability(cls, db, consultant_id):
        """
        Get all availability for a consultant grouped by date

        Args:
            db: Database session
            consultant_id: Consultant ID

        Returns:
            Dictionary with consultant_id and dates with availability slots
        """
        # Query all availability slots for the consultant that aren't booked
        availabilities = (
            db.query(cls)
            .filter(
                cls.consultant_id == consultant_id,
                cls.is_booked == False,
                cls.start_time > datetime.now(),  # Only future slots
            )
            .order_by(cls.start_time)
            .all()
        )

        # Group by date
        return cls.group_by_date(availabilities)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "consultant_id": self.consultant_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "is_booked": self.is_booked,
        }
