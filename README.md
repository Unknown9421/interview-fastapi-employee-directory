# FastAPI Employee Search Service

A high-performance, containerized microservice built with **FastAPI** to provide an employee search directory. Designed for multi-tenancy, high scalability (millions of users), and dynamic configuration.

> **Note:** This project is a technical assignment solution focusing on API design, performance optimization, and custom implementation of core system components without external dependencies.

---

## Key Features

* **High-Performance API:** Optimized with Deferred Join (Late Row Lookup) pagination for handling millions of records (10x-100x faster for deep pages).
* **Multi-Select Filters:** Support for selecting multiple values in location, company, department, position filters.
* **Full-Text Search:** PostgreSQL tsvector-based search on name and email fields.
* **Page Jumping:** Traditional pagination with page numbers - jump to any page directly.
* **Multi-Tenancy Isolation:** Strict data separation ensures users can only search within their own organization.
* **Dynamic Column Configuration:** Return fields are dynamically masked based on per-organization settings.
* **Custom Rate Limiting:** Thread-safe, in-memory sliding window rate limiter (no Redis/external libs).
* **Containerized:** Fully Dockerized with optimized multi-stage builds.
* **OpenAPI Integration:** Auto-generated API documentation via Swagger UI.

---

## Tech Stack

* **Language:** Python 3.11+
* **Framework:** FastAPI 0.121+
* **Database:** PostgreSQL 16 (via SQLAlchemy 2.0 Async & AsyncPG)
* **Container:** Docker & Docker Compose
* **Testing:** Pytest with pytest-asyncio

---

## Architecture Decisions

### 1. Dynamic Columns (The "Configurable Output" Problem)
Instead of hardcoding the API response model, the system uses a configuration layer.
* **Storage:** Organization configurations (allowed columns) are stored in the database.
* **Logic:** A serializer layer filters out fields that are not in the organization's "allow-list". This ensures that even if the DB query selects all data, the API response remains strict and secure.

### 2. Deferred Join Pagination (High Performance)
Traditional OFFSET pagination is slow for deep pages because it reads and discards N rows.
* **Implementation:** Split query into 2 steps: (1) Get IDs using index-only scan, (2) JOIN back to fetch full data.
* **Performance:** 10x-100x faster for pages 1000+ compared to simple OFFSET.
* **Page Jumping:** Supports jumping to any page directly (unlike cursor-based pagination).

### 3. Custom Rate Limiting (No External Libs)
Per the assignment constraints, no external rate-limiting libraries (like `slowapi` or Redis) were used.
* **Implementation:** A **Sliding Window** algorithm using Python's `collections` and `time` modules.
* **Concurrency:** Used `asyncio.Lock` to ensure thread safety when modifying the in-memory request counters.
* **Cleanup:** A background mechanism periodically cleans up stale entries to prevent memory leaks.

---

## Quick Start

### Prerequisites
* Docker & Docker Compose installed on your machine.

### Running with Docker (Recommended)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Unknown9421/interview-fastapi-employee-directory.git
    cd interview-fastapi-employee-directory
    ```

2.  **Start the services:**
    ```bash
    docker-compose up --build
    ```
    This will:
    - Build Docker image for the application
    - Start PostgreSQL 16 (port 5436)
    - Run database migrations
    - Seed **10,000 employees** randomly
    - Start FastAPI server (port 8000)

3.  **Access the API:**
    * **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
    * **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
    * **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

4.  **Stop services:**
    ```bash
    docker-compose down
    ```

    To also remove database volume:
    ```bash
    docker-compose down -v
    ```

---

## API Usage

### Required Header

All requests to `/api/v1/employees` require:
```
X-Organization-ID: <organization_id>
```

### Example Requests

**Get employees (excludes terminated by default):**
```bash
curl -X GET "http://localhost:8000/api/v1/employees" \
  -H "X-Organization-ID: 1"
```

**With filters:**
```bash
curl -X GET "http://localhost:8000/api/v1/employees?status=Active&department=Engineering&page=1&page_size=20" \
  -H "X-Organization-ID: 1"
```

**Include terminated employees:**
```bash
curl -X GET "http://localhost:8000/api/v1/employees?include_terminated=true" \
  -H "X-Organization-ID: 1"
```

**Multi-select filters:**
```bash
curl -X GET "http://localhost:8000/api/v1/employees?department=Engineering&department=Marketing&location=New%20York" \
  -H "X-Organization-ID: 1"
```

**Text search:**
```bash
curl -X GET "http://localhost:8000/api/v1/employees?search=john" \
  -H "X-Organization-ID: 1"
```

**Get filter options:**
```bash
curl -X GET "http://localhost:8000/api/v1/employees/filters" \
  -H "X-Organization-ID: 1"
```

### Response Format

```json
{
  "items": [
    {
      "id": 1,
      "avatar_url": "https://ui-avatars.com/api/?name=John+Doe",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@techcorp.com",
      "phone": "+1-555-0101",
      "status": "Active",
      "location": "New York, NY",
      "company": "Main Branch",
      "department": "Engineering",
      "position": "Software Engineer"
    }
  ],
  "pagination": {
    "total": 10000,
    "page": 1,
    "page_size": 50,
    "total_pages": 200
  }
}
```

---

## Shell Scripts

Helper scripts in the `scripts/` directory:

| Script | Description | Usage |
|--------|-------------|-------|
| `init-db.sh` | Initialize database (migrations + seed) | `./scripts/init-db.sh` |
| `start.sh` | Start app with auto-initialization | `./scripts/start.sh` |
| `migrate.sh` | Migration helper commands | `./scripts/migrate.sh [command]` |
| `test.sh` | Run tests with coverage | `./scripts/test.sh` |
| `dev.sh` | Development server with reload | `./scripts/dev.sh` |

### Migration Commands

```bash
./scripts/migrate.sh create "migration_name"  # Create new migration
./scripts/migrate.sh upgrade                  # Apply all migrations
./scripts/migrate.sh downgrade                # Rollback last migration
./scripts/migrate.sh reset                    # Reset database
./scripts/migrate.sh history                  # Show migration history
./scripts/migrate.sh current                  # Show current revision
```

---

## Testing

Run tests inside the container:

```bash
docker-compose exec app pytest -v
```

With coverage report:

```bash
docker-compose exec app pytest --cov=app --cov-report=term-missing
```

---

## Project Structure

```
├── app/
│   ├── api/              # API endpoints
│   │   └── employees.py  # Employee search endpoint
│   ├── core/             # Core dependencies
│   │   └── dependencies.py
│   ├── middleware/       # Custom middleware
│   │   └── rate_limiter.py
│   ├── models/           # SQLAlchemy models
│   │   ├── employee.py
│   │   └── organization.py
│   ├── schemas/          # Pydantic schemas (DTOs)
│   │   ├── employee.py
│   │   └── organization.py
│   ├── services/         # Business logic
│   │   └── employee_service.py
│   ├── main.py           # FastAPI application
│   ├── config.py         # Settings
│   ├── database.py       # Database connection
│   └── seed_data.py      # Seed script (10,000 records)
├── alembic/              # Database migrations
│   └── versions/
├── scripts/              # Shell scripts
├── tests/                # Unit tests
│   ├── conftest.py       # Test fixtures
│   ├── test_api.py       # API tests
│   └── test_rate_limiter.py
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
├── requirements.txt
└── .env.example
```

---

## Sample Data

After seeding, the system has **10,000 employees** distributed as:

| Organization ID | Name | Visible Columns | ~Employees |
|----------------|------|-----------------|------------|
| 1 | TechCorp International | All columns | ~5,000 (50%) |
| 2 | HealthFirst Medical | No phone, location, company | ~3,000 (30%) |
| 3 | EduLearn Academy | Basic info only | ~2,000 (20%) |

**Distribution:**
- 70% Active, 20% Not started, 10% Terminated
- Data inserted in batches (500 records/batch) for performance

---

## Rate Limiting

API rate limiting configuration:
- **100 requests / 60 seconds** (default)
- Response headers:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Window`: Time window (seconds)

Exceeding the limit returns `429 Too Many Requests`.

---

## Troubleshooting

### Database connection error

```
sqlalchemy.exc.OperationalError: connection refused
```

**Solution:** Ensure PostgreSQL is running and DATABASE_URL is correct.

### Migration error

```bash
# Reset migrations
alembic downgrade base
alembic upgrade head
```

### Clear all data and restart

```bash
docker-compose down -v
docker-compose up --build
```

---

## License

This project is for technical assessment purposes.
