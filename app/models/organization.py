from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY

from app.models.base import AuditableModel, TimestampMixin
from app.database import Base


class Organization(AuditableModel):
    """Organization model with audit capabilities."""
    __tablename__ = "organizations"

    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, server_default="true")

    # Relationships
    employees = relationship("Employee", back_populates="organization", lazy="selectin")
    config = relationship("OrganizationConfig", back_populates="organization", uselist=False, lazy="selectin")


class OrganizationConfig(Base, TimestampMixin):
    """Configuration for organization-specific settings like visible columns."""
    __tablename__ = "organization_configs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Dynamic columns configuration - list of allowed column names
    visible_columns = Column(ARRAY(String), nullable=False, default=[
        "id", "first_name", "last_name", "email", "phone", "status",
        "location", "company", "department", "position", "avatar_url"
    ])

    # Relationship
    organization = relationship("Organization", back_populates="config")
