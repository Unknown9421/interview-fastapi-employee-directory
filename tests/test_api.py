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
async def test_list_employees_without_org_header(client: AsyncClient):
    """Test list endpoint requires organization header."""
    response = await client.get("/api/v1/employees")
    assert response.status_code == 422  # Missing required header


@pytest.mark.asyncio
async def test_list_employees_invalid_organization(client: AsyncClient):
    """Test list with non-existent organization."""
    response = await client.get(
        "/api/v1/employees",
        headers={"X-Organization-ID": "99999"}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ==================== List Employees Tests ====================

@pytest.mark.asyncio
async def test_list_employees_basic(
    client: AsyncClient,
    sample_organization: Organization,
    sample_employees: list[Employee]
):
    """Test basic employee listing."""
    response = await client.get(
        "/api/v1/employees",
        headers={"X-Organization-ID": str(sample_organization.id)}
    )
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "pagination" in data
    assert "total" in data["pagination"]
    assert "page" in data["pagination"]
    assert "page_size" in data["pagination"]
    assert "total_pages" in data["pagination"]

    # By default, terminated employees are excluded (3 out of 4)
    assert data["pagination"]["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_list_employees_pagination(
    client: AsyncClient,
    sample_organization: Organization,
    sample_employees: list[Employee]
):
    """Test pagination with page numbers."""
    # First page with page_size 2
    response = await client.get(
        "/api/v1/employees",
        headers={"X-Organization-ID": str(sample_organization.id)},
        params={"page": 1, "page_size": 2}
    )
    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 2
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["total_pages"] == 2

    # Second page
    response = await client.get(
        "/api/v1/employees",
        headers={"X-Organization-ID": str(sample_organization.id)},
        params={"page": 2, "page_size": 2}
    )
    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 1  # Only 1 remaining
    assert data["pagination"]["page"] == 2


@pytest.mark.asyncio
async def test_list_employees_text_search(
    client: AsyncClient,
    sample_organization: Organization,
    sample_employees: list[Employee]
):
    """Test text search functionality."""
    # Search by unique email (more specific than name to avoid seed data conflicts)
    response = await client.get(
        "/api/v1/employees",
        headers={"X-Organization-ID": str(sample_organization.id)},
        params={"q": "john.doe@test.com"}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["pagination"]["total"] == 1
    assert data["items"][0]["first_name"] == "John"
    assert data["items"][0]["email"] == "john.doe@test.com"


@pytest.mark.asyncio
async def test_list_employees_include_terminated(
    client: AsyncClient,
    sample_organization: Organization,
    sample_employees: list[Employee]
):
    """Test including terminated employees."""
    response = await client.get(
        "/api/v1/employees",
        headers={"X-Organization-ID": str(sample_organization.id)},
        params={"include_terminated": "true"}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["pagination"]["total"] == 4


@pytest.mark.asyncio
async def test_list_employees_filter_by_status(
    client: AsyncClient,
    sample_organization: Organization,
    sample_employees: list[Employee]
):
    """Test status filter."""
    response = await client.get(
        "/api/v1/employees",
        headers={"X-Organization-ID": str(sample_organization.id)},
        params={"status": "Active"}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["pagination"]["total"] == 2
    for item in data["items"]:
        assert item["status"] == "Active"


@pytest.mark.asyncio
async def test_list_employees_multiple_status(
    client: AsyncClient,
    sample_organization: Organization,
    sample_employees: list[Employee]
):
    """Test multiple status selection."""
    response = await client.get(
        "/api/v1/employees",
        headers={"X-Organization-ID": str(sample_organization.id)},
        params={"status": ["Active", "Not started"]}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["pagination"]["total"] == 3


@pytest.mark.asyncio
async def test_list_employees_filter_department(
    client: AsyncClient,
    sample_organization: Organization,
    sample_employees: list[Employee]
):
    """Test department filter."""
    response = await client.get(
        "/api/v1/employees",
        headers={"X-Organization-ID": str(sample_organization.id)},
        params={"department": "Engineering"}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["pagination"]["total"] == 2
    for item in data["items"]:
        assert item["department"] == "Engineering"


@pytest.mark.asyncio
async def test_list_employees_multi_select_department(
    client: AsyncClient,
    sample_organization: Organization,
    sample_employees: list[Employee]
):
    """Test multi-select department filter."""
    response = await client.get(
        "/api/v1/employees",
        headers={"X-Organization-ID": str(sample_organization.id)},
        params={"department": ["Engineering", "Marketing"]}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["pagination"]["total"] == 3
    departments = [item["department"] for item in data["items"]]
    for dept in departments:
        assert dept in ["Engineering", "Marketing"]


@pytest.mark.asyncio
async def test_list_employees_multi_select_location(
    client: AsyncClient,
    sample_organization: Organization,
    sample_employees: list[Employee]
):
    """Test multi-select location filter."""
    response = await client.get(
        "/api/v1/employees",
        headers={"X-Organization-ID": str(sample_organization.id)},
        params={"location": ["New York, NY", "Los Angeles, CA"]}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["pagination"]["total"] == 2
    locations = [item["location"] for item in data["items"]]
    for loc in locations:
        assert loc in ["New York, NY", "Los Angeles, CA"]


@pytest.mark.asyncio
async def test_list_employees_dynamic_columns(
    client: AsyncClient,
    sample_organization: Organization,
    sample_employees: list[Employee]
):
    """Test dynamic column filtering."""
    response = await client.get(
        "/api/v1/employees",
        headers={"X-Organization-ID": str(sample_organization.id)}
    )
    assert response.status_code == 200
    data = response.json()

    # Based on sample_organization config
    for item in data["items"]:
        assert "phone" not in item
        assert "company" not in item
        assert "id" in item
        assert "first_name" in item


@pytest.mark.asyncio
async def test_list_employees_combined_filters(
    client: AsyncClient,
    sample_organization: Organization,
    sample_employees: list[Employee]
):
    """Test combining multiple filters."""
    response = await client.get(
        "/api/v1/employees",
        headers={"X-Organization-ID": str(sample_organization.id)},
        params={
            "status": "Active",
            "department": "Engineering"
        }
    )
    assert response.status_code == 200
    data = response.json()

    assert data["pagination"]["total"] == 1
    assert data["items"][0]["first_name"] == "John"
    assert data["items"][0]["department"] == "Engineering"
    assert data["items"][0]["status"] == "Active"


# ==================== Filter Options Tests ====================

@pytest.mark.asyncio
async def test_get_filter_options(
    client: AsyncClient,
    sample_organization: Organization,
    sample_employees: list[Employee]
):
    """Test get filter options endpoint."""
    response = await client.get(
        "/api/v1/employees/filters",
        headers={"X-Organization-ID": str(sample_organization.id)}
    )
    assert response.status_code == 200
    data = response.json()

    assert "locations" in data
    assert "companies" in data
    assert "departments" in data
    assert "positions" in data
    assert "statuses" in data

    # Should have distinct values from sample employees
    assert len(data["locations"]) > 0
    assert len(data["departments"]) > 0
    assert "Active" in data["statuses"]


@pytest.mark.asyncio
async def test_get_filter_options_invalid_org(client: AsyncClient):
    """Test filter options with invalid organization."""
    response = await client.get(
        "/api/v1/employees/filters",
        headers={"X-Organization-ID": "99999"}
    )
    assert response.status_code == 404


# ==================== Rate Limiting Tests ====================

@pytest.mark.asyncio
async def test_rate_limit_headers(
    client: AsyncClient,
    sample_organization: Organization,
    sample_employees: list[Employee]
):
    """Test rate limit headers in response."""
    response = await client.get(
        "/api/v1/employees",
        headers={"X-Organization-ID": str(sample_organization.id)}
    )
    assert response.status_code == 200

    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Window" in response.headers
