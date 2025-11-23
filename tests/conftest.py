import pytest
import asyncio
import os
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.organization import Organization, OrganizationConfig
from app.models.employee import Employee, EmployeeStatus

# Test database URL - use PostgreSQL (same as app, supports ARRAY type)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@db:5432/employee_directory"
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine (session-scoped to avoid recreation)."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session with transaction rollback.
    Each test runs in a transaction that gets rolled back after.
    This preserves the database state (including seed data).
    """
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with test_engine.connect() as conn:
        # Start a transaction
        trans = await conn.begin()

        # Create a session bound to this connection
        async with async_session(bind=conn) as session:
            yield session

        # Rollback the transaction (undo all changes)
        await trans.rollback()


@pytest.fixture(scope="function")
async def client(test_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with overridden dependencies."""

    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def sample_organization(test_session: AsyncSession) -> Organization:
    """Create a sample organization for testing."""
    org = Organization(
        name="Test Organization",
        description="Test organization for unit tests",
        is_active=True
    )
    test_session.add(org)
    await test_session.flush()

    config = OrganizationConfig(
        organization_id=org.id,
        visible_columns=[
            "id", "first_name", "last_name", "email",
            "status", "location", "department", "position"
        ]
    )
    test_session.add(config)
    await test_session.commit()

    return org


@pytest.fixture
async def sample_employees(test_session: AsyncSession, sample_organization: Organization) -> list[Employee]:
    """Create sample employees for testing."""
    employees = [
        Employee(
            organization_id=sample_organization.id,
            avatar_url="https://ui-avatars.com/api/?name=John+Doe",
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
            phone="+1-555-0101",
            status=EmployeeStatus.ACTIVE,
            location="New York, NY",
            company="Main Branch",
            department="Engineering",
            position="Software Engineer",
            is_deleted=False,
        ),
        Employee(
            organization_id=sample_organization.id,
            avatar_url="https://ui-avatars.com/api/?name=Jane+Smith",
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@test.com",
            phone="+1-555-0102",
            status=EmployeeStatus.ACTIVE,
            location="Los Angeles, CA",
            company="West Division",
            department="Marketing",
            position="Marketing Specialist",
            is_deleted=False,
        ),
        Employee(
            organization_id=sample_organization.id,
            avatar_url="https://ui-avatars.com/api/?name=Bob+Johnson",
            first_name="Bob",
            last_name="Johnson",
            email="bob.johnson@test.com",
            phone="+1-555-0103",
            status=EmployeeStatus.NOT_STARTED,
            location="Chicago, IL",
            company="Main Branch",
            department="Engineering",
            position="Senior Developer",
            is_deleted=False,
        ),
        Employee(
            organization_id=sample_organization.id,
            avatar_url="https://ui-avatars.com/api/?name=Alice+Williams",
            first_name="Alice",
            last_name="Williams",
            email="alice.williams@test.com",
            phone="+1-555-0104",
            status=EmployeeStatus.TERMINATED,
            location="New York, NY",
            company="East Division",
            department="Sales",
            position="Sales Representative",
            is_deleted=False,
        ),
    ]

    for emp in employees:
        test_session.add(emp)

    await test_session.commit()
    return employees
