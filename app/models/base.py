"""
Base models and mixins for audit logging and common functionality.
These provide a foundation for all database models in the application.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from sqlalchemy.ext.declarative import declared_attr

from app.database import Base


class TimestampMixin:
    """Mixin for automatic timestamp tracking."""

    @declared_attr
    def created_at(cls):
        return Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            doc="Timestamp when the record was created"
        )

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
            doc="Timestamp when the record was last updated"
        )


class AuditMixin(TimestampMixin):
    """
    Mixin for audit logging - tracks who created/modified records.
    Extends TimestampMixin with user tracking.
    """

    @declared_attr
    def created_by(cls):
        return Column(
            String(255),
            nullable=True,
            doc="User/system that created this record"
        )

    @declared_attr
    def updated_by(cls):
        return Column(
            String(255),
            nullable=True,
            doc="User/system that last updated this record"
        )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    @declared_attr
    def is_deleted(cls):
        return Column(
            Boolean,
            nullable=False,
            default=False,
            server_default="false",
            doc="Flag indicating if the record is soft deleted"
        )

    @declared_attr
    def deleted_at(cls):
        return Column(
            DateTime(timezone=True),
            nullable=True,
            doc="Timestamp when the record was soft deleted"
        )

    @declared_attr
    def deleted_by(cls):
        return Column(
            String(255),
            nullable=True,
            doc="User/system that deleted this record"
        )


class BaseModel(Base):
    """
    Abstract base model with ID and timestamps.
    All models should inherit from this.
    """
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)


class AuditableModel(BaseModel, AuditMixin):
    """
    Abstract base model with full audit capabilities.
    Use this for models that need audit logging.
    """
    __abstract__ = True


class SoftDeletableModel(AuditableModel, SoftDeleteMixin):
    """
    Abstract base model with audit and soft delete capabilities.
    Use this for models that should never be hard deleted.
    """
    __abstract__ = True
