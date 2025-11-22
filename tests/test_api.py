import pytest
from httpx import AsyncClient

from app.models.organization import Organization
from app.models.employee import Employee


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint returns API information."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["docs"] == "/docs"


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_search_without_org_header(client: AsyncClient):
    """Test search endpoint requires organization header."""
    response = await client.get("/api/v1/employees/search")
    assert response.status_code == 422  # Missing required header


@pytest.mark.asyncio
async def test_search_invalid_organization(client: AsyncClient):
    """Test search with non-existent organization."""
    response = await client.get(
        "/api/v1/employees/search",
        headers={"X-Organization-ID": "99999"}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_search_employees_basic(
    client: AsyncClient,
    sample_organization: Organization,
    sample_employees: list[Employee]
):
    """Test basic employee search."""
    response = await client.get(
        "/api/v1/employees/search",
        headers={"X-Organization-ID": str(sample_organization.id)}
    )
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data

    assert data["total"] == len(sample_employees)
    assert len(data["items"]) == len(sample_employees)


@pytest.mark.asyncio
async def test_search_employees_filter_by_status(
    client: AsyncClient,
    sample_organization: Organization,
    sample_employees: list[Employee]
):
    """Test employee search with status filter."""
    response = await client.get(
        "/api/v1/employees/search",
        headers={"X-Organization-ID": str(sample_organization.id)},
        params={"status": "Active"}
    )
    assert response.status_code == 200
    data = response.json()

    # Should only return active employees
    assert data["total"] == 2
    for item in data["items"]:
        assert item["status"] == "Active"


@pytest.mark.asyncio
async def test_search_employees_filter_by_department(
    client: AsyncClient,
    sample_organization: Organization,
    sample_employees: list[Employee]
):
    """Test employee search with department filter."""
    response = await client.get(
        "/api/v1/employees/search",
        headers={"X-Organization-ID": str(sample_organization.id)},
        params={"department": "Engineering"}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2
    for item in data["items"]:
        assert "Engineering" in item["department"]


@pytest.mark.asyncio
async def test_search_employees_filter_by_location(
    client: AsyncClient,
    sample_organization: Organization,
    sample_employees: list[Employee]
):
    """Test employee search with location filter."""
    response = await client.get(
        "/api/v1/employees/search",
        headers={"X-Organization-ID": str(sample_organization.id)},
        params={"location": "New York"}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2
    for item in data["items"]:
        assert "New York" in item["location"]


@pytest.mark.asyncio
async def test_search_employees_pagination(
    client: AsyncClient,
    sample_organization: Organization,
    sample_employees: list[Employee]
):
    """Test employee search pagination."""
    # Request page 1 with page_size 2
    response = await client.get(
        "/api/v1/employees/search",
        headers={"X-Organization-ID": str(sample_organization.id)},
        params={"page": 1, "page_size": 2}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 4
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_pages"] == 2


@pytest.mark.asyncio
async def test_search_employees_dynamic_columns(
    client: AsyncClient,
    sample_organization: Organization,
    sample_employees: list[Employee]
):
    """Test that response only includes configured visible columns."""
    response = await client.get(
        "/api/v1/employees/search",
        headers={"X-Organization-ID": str(sample_organization.id)}
    )
    assert response.status_code == 200
    data = response.json()

    # Check that phone and company are NOT in the response
    # (based on sample_organization config)
    for item in data["items"]:
        assert "phone" not in item
        assert "company" not in item
        # These should be present
        assert "id" in item
        assert "first_name" in item
        assert "last_name" in item


@pytest.mark.asyncio
async def test_search_employees_combined_filters(
    client: AsyncClient,
    sample_organization: Organization,
    sample_employees: list[Employee]
):
    """Test employee search with multiple filters."""
    response = await client.get(
        "/api/v1/employees/search",
        headers={"X-Organization-ID": str(sample_organization.id)},
        params={
            "status": "Active",
            "location": "New York"
        }
    )
    assert response.status_code == 200
    data = response.json()

    # Only John Doe matches both criteria
    assert data["total"] == 1
    assert data["items"][0]["first_name"] == "John"


@pytest.mark.asyncio
async def test_rate_limit_headers(
    client: AsyncClient,
    sample_organization: Organization,
    sample_employees: list[Employee]
):
    """Test that rate limit headers are present in response."""
    response = await client.get(
        "/api/v1/employees/search",
        headers={"X-Organization-ID": str(sample_organization.id)}
    )
    assert response.status_code == 200

    # Check rate limit headers
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Window" in response.headers
