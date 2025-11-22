"""Initial migration - create tables with audit support

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create organizations table with audit fields
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)

    # Create organization_configs table with timestamps
    op.create_table(
        'organization_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('visible_columns', postgresql.ARRAY(sa.String()), nullable=False),
        # Timestamp fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id')
    )
    op.create_index(op.f('ix_organization_configs_id'), 'organization_configs', ['id'], unique=False)

    # Create employees table with full audit and soft delete
    op.create_table(
        'employees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        # Profile info
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        # Contact info
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        # Work info
        sa.Column('status', sa.Enum('ACTIVE', 'NOT_STARTED', 'TERMINATED', name='employeestatus'), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('company', sa.String(length=255), nullable=True),
        sa.Column('department', sa.String(length=255), nullable=True),
        sa.Column('position', sa.String(length=255), nullable=True),
        # Additional info
        sa.Column('notes', sa.Text(), nullable=True),
        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        # Soft delete fields
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_employees_id'), 'employees', ['id'], unique=False)
    op.create_index(op.f('ix_employees_organization_id'), 'employees', ['organization_id'], unique=False)

    # Create composite indexes for search optimization
    op.create_index('ix_employees_org_status', 'employees', ['organization_id', 'status'], unique=False)
    op.create_index('ix_employees_org_location', 'employees', ['organization_id', 'location'], unique=False)
    op.create_index('ix_employees_org_company', 'employees', ['organization_id', 'company'], unique=False)
    op.create_index('ix_employees_org_department', 'employees', ['organization_id', 'department'], unique=False)
    op.create_index('ix_employees_org_position', 'employees', ['organization_id', 'position'], unique=False)
    op.create_index('ix_employees_org_deleted', 'employees', ['organization_id', 'is_deleted'], unique=False)
    op.create_index('ix_employees_search', 'employees',
                    ['organization_id', 'status', 'location', 'company', 'department', 'position'],
                    unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_employees_search', table_name='employees')
    op.drop_index('ix_employees_org_deleted', table_name='employees')
    op.drop_index('ix_employees_org_position', table_name='employees')
    op.drop_index('ix_employees_org_department', table_name='employees')
    op.drop_index('ix_employees_org_company', table_name='employees')
    op.drop_index('ix_employees_org_location', table_name='employees')
    op.drop_index('ix_employees_org_status', table_name='employees')
    op.drop_index(op.f('ix_employees_organization_id'), table_name='employees')
    op.drop_index(op.f('ix_employees_id'), table_name='employees')

    # Drop tables
    op.drop_table('employees')
    op.drop_index(op.f('ix_organization_configs_id'), table_name='organization_configs')
    op.drop_table('organization_configs')
    op.drop_index(op.f('ix_organizations_id'), table_name='organizations')
    op.drop_table('organizations')

    # Drop enum type
    sa.Enum(name='employeestatus').drop(op.get_bind())
