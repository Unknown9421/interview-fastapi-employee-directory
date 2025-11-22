from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY

from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    employees = relationship("Employee", back_populates="organization", lazy="selectin")
    config = relationship("OrganizationConfig", back_populates="organization", uselist=False, lazy="selectin")


class OrganizationConfig(Base):
    __tablename__ = "organization_configs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Dynamic columns configuration - list of allowed column names
    visible_columns = Column(ARRAY(String), nullable=False, default=[
        "id", "first_name", "last_name", "email", "status",
        "location", "company", "department", "position"
    ])

    # Relationship
    organization = relationship("Organization", back_populates="config")
