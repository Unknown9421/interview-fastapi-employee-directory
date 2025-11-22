from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Core employee fields
    employee_id = Column(String(50), nullable=False)  # Organization's internal employee ID
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    department = Column(String(100), nullable=True, index=True)
    position = Column(String(100), nullable=True, index=True)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    hire_date = Column(DateTime(timezone=True), nullable=True)

    # Dynamic fields stored as JSONB for flexibility
    custom_fields = Column(JSONB, default=dict, nullable=False)

    # Metadata
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="employees")
    manager = relationship("Employee", remote_side=[id], backref="direct_reports")

    # Composite indexes for optimized search
    __table_args__ = (
        Index("ix_employees_org_employee_id", "organization_id", "employee_id", unique=True),
        Index("ix_employees_org_email", "organization_id", "email"),
        Index("ix_employees_org_name", "organization_id", "first_name", "last_name"),
        Index("ix_employees_org_department", "organization_id", "department"),
        Index("ix_employees_org_active", "organization_id", "is_active"),
        # GIN index for JSONB custom_fields for fast JSON queries
        Index("ix_employees_custom_fields", "custom_fields", postgresql_using="gin"),
    )

    def __repr__(self):
        return f"<Employee(id={self.id}, name={self.first_name} {self.last_name})>"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
