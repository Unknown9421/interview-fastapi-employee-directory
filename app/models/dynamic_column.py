from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class ColumnType(str, enum.Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    SELECT = "select"  # For dropdown options


class DynamicColumn(Base):
    __tablename__ = "dynamic_columns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Column configuration
    name = Column(String(100), nullable=False)  # Internal name (e.g., "employee_badge")
    display_name = Column(String(255), nullable=False)  # User-friendly name (e.g., "Employee Badge Number")
    column_type = Column(Enum(ColumnType), nullable=False, default=ColumnType.STRING)

    # Validation and display
    is_required = Column(Boolean, default=False, nullable=False)
    is_searchable = Column(Boolean, default=True, nullable=False)
    is_visible = Column(Boolean, default=True, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)

    # For SELECT type - comma-separated options
    options = Column(String(1000), nullable=True)

    # Default value
    default_value = Column(String(500), nullable=True)

    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="dynamic_columns")

    __table_args__ = (
        Index("ix_dynamic_columns_org_name", "organization_id", "name", unique=True),
        Index("ix_dynamic_columns_org_order", "organization_id", "display_order"),
    )

    def __repr__(self):
        return f"<DynamicColumn(id={self.id}, name={self.name}, type={self.column_type})>"
