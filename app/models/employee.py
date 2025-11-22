from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Index, Text
from sqlalchemy.orm import relationship
import enum

from app.models.base import SoftDeletableModel


class EmployeeStatus(str, enum.Enum):
    ACTIVE = "Active"
    NOT_STARTED = "Not started"
    TERMINATED = "Terminated"


class Employee(SoftDeletableModel):
    """
    Employee model with full audit and soft delete capabilities.
    Supports multi-tenancy through organization_id.
    """
    __tablename__ = "employees"

    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Profile info
    avatar_url = Column(String(500), nullable=True, doc="URL to employee's profile picture")
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    # Contact info
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)

    # Work info - filterable fields
    status = Column(Enum(EmployeeStatus), nullable=False, default=EmployeeStatus.ACTIVE)
    location = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    position = Column(String(255), nullable=True)

    # Additional info
    notes = Column(Text, nullable=True, doc="Internal notes about the employee")

    # Relationship
    organization = relationship("Organization", back_populates="employees")

    # Indexes for performance optimization
    __table_args__ = (
        Index("ix_employees_org_status", "organization_id", "status"),
        Index("ix_employees_org_location", "organization_id", "location"),
        Index("ix_employees_org_company", "organization_id", "company"),
        Index("ix_employees_org_department", "organization_id", "department"),
        Index("ix_employees_org_position", "organization_id", "position"),
        Index("ix_employees_org_deleted", "organization_id", "is_deleted"),
        Index("ix_employees_search", "organization_id", "status", "location", "company", "department", "position"),
    )
