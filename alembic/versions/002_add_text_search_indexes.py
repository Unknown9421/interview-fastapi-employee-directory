"""Add text search indexes

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Indexes for text search (first_name, last_name, email)
    op.create_index(
        'ix_employees_first_name',
        'employees',
        ['first_name'],
        unique=False
    )
    op.create_index(
        'ix_employees_last_name',
        'employees',
        ['last_name'],
        unique=False
    )
    op.create_index(
        'ix_employees_email',
        'employees',
        ['email'],
        unique=False
    )

    # Composite index for text search with organization
    op.create_index(
        'ix_employees_org_name_search',
        'employees',
        ['organization_id', 'first_name', 'last_name'],
        unique=False
    )

    # Index for filter dropdown queries (distinct values)
    op.create_index(
        'ix_employees_org_location_distinct',
        'employees',
        ['organization_id', 'location'],
        unique=False,
        postgresql_where='location IS NOT NULL'
    )
    op.create_index(
        'ix_employees_org_company_distinct',
        'employees',
        ['organization_id', 'company'],
        unique=False,
        postgresql_where='company IS NOT NULL'
    )
    op.create_index(
        'ix_employees_org_department_distinct',
        'employees',
        ['organization_id', 'department'],
        unique=False,
        postgresql_where='department IS NOT NULL'
    )
    op.create_index(
        'ix_employees_org_position_distinct',
        'employees',
        ['organization_id', 'position'],
        unique=False,
        postgresql_where='position IS NOT NULL'
    )


def downgrade() -> None:
    op.drop_index('ix_employees_org_position_distinct', table_name='employees')
    op.drop_index('ix_employees_org_department_distinct', table_name='employees')
    op.drop_index('ix_employees_org_company_distinct', table_name='employees')
    op.drop_index('ix_employees_org_location_distinct', table_name='employees')
    op.drop_index('ix_employees_org_name_search', table_name='employees')
    op.drop_index('ix_employees_email', table_name='employees')
    op.drop_index('ix_employees_last_name', table_name='employees')
    op.drop_index('ix_employees_first_name', table_name='employees')
