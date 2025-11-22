# Employee Directory API

High-performance Employee Search Microservice built with FastAPI. Features dynamic column configuration per organization, multi-tenancy security, and a custom in-memory rate-limiting implementation (no external libs). Designed for millions of records.

## Features

- **High-Performance Search**: Optimized queries with composite indexes for searching millions of records
- **Dynamic Column Configuration**: Each organization can define custom fields for employees
- **Multi-tenancy Security**: API key-based authentication with organization isolation
- **Custom In-Memory Rate Limiting**: Pure Python implementation without external libraries
- **Async Support**: Full async/await support with asyncpg for PostgreSQL

## Tech Stack

- **Framework**: FastAPI 0.121.3
- **Database**: PostgreSQL 16+ with asyncpg
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic 1.17.2
- **Validation**: Pydantic 2.x

## Project Structure

```
├── app/
│   ├── core/           # Configuration and database setup
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── routers/        # API endpoints
│   ├── services/       # Business logic
│   ├── middleware/     # Rate limiting, tenant middleware
│   └── main.py         # Application entry point
├── alembic/            # Database migrations
├── tests/              # Test files
├── requirements.txt    # Dependencies
└── .env.example        # Environment variables template
```

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd interview-fastapi-employee-directory
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

5. **Create database**
```bash
createdb employee_directory
```

6. **Run migrations**
```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

7. **Start the server**
```bash
uvicorn app.main:app --reload
```

## API Documentation

Once running, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Quick Start

### 1. Create an Organization (Admin)

```bash
curl -X POST "http://localhost:8000/admin/organizations" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation",
    "slug": "acme-corp",
    "description": "Main organization"
  }'
```

### 2. Create an API Key (Admin)

```bash
curl -X POST "http://localhost:8000/admin/organizations/{org_id}/api-keys" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API Key",
    "description": "Main API key for production"
  }'
```

Save the returned API key - it's only shown once!

### 3. Create Employees

```bash
curl -X POST "http://localhost:8000/employees" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "employee_id": "EMP001",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "department": "Engineering",
    "position": "Software Engineer"
  }'
```

### 4. Search Employees

```bash
curl -X POST "http://localhost:8000/employees/search" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "query": "john",
    "department": "Engineering"
  }'
```

## Dynamic Columns

Organizations can define custom fields that appear in employee `custom_fields`:

```bash
# Create a dynamic column
curl -X POST "http://localhost:8000/columns" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "name": "badge_number",
    "display_name": "Badge Number",
    "column_type": "string",
    "is_required": true
  }'

# Create employee with custom field
curl -X POST "http://localhost:8000/employees" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "employee_id": "EMP002",
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@example.com",
    "custom_fields": {
      "badge_number": "B12345"
    }
  }'
```

## Rate Limiting

- Default: 100 requests per 60 seconds
- Applied per API key or IP address
- Headers returned with each response:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Seconds until limit resets

## API Endpoints

### Admin (No Auth Required)
- `POST /admin/organizations` - Create organization
- `GET /admin/organizations` - List organizations
- `POST /admin/organizations/{id}/api-keys` - Create API key

### Organization (Auth Required)
- `GET /organization/me` - Get current organization

### Employees (Auth Required)
- `GET /employees` - List employees (paginated)
- `POST /employees` - Create employee
- `POST /employees/search` - Search employees
- `POST /employees/bulk` - Bulk create employees
- `GET /employees/{id}` - Get employee
- `PATCH /employees/{id}` - Update employee
- `DELETE /employees/{id}` - Delete employee
- `GET /employees/departments` - List departments
- `GET /employees/positions` - List positions

### Dynamic Columns (Auth Required)
- `GET /columns` - List columns
- `POST /columns` - Create column
- `GET /columns/{id}` - Get column
- `PATCH /columns/{id}` - Update column
- `DELETE /columns/{id}` - Delete column
- `POST /columns/reorder` - Reorder columns

### API Keys (Auth Required)
- `GET /api-keys` - List API keys
- `POST /api-keys` - Create API key
- `POST /api-keys/{id}/deactivate` - Deactivate key
- `DELETE /api-keys/{id}` - Delete key

## Performance Optimization

The application is optimized for handling millions of records:

1. **Composite Indexes**: Strategic indexes on frequently queried columns
2. **GIN Index on JSONB**: Fast queries on custom_fields
3. **Connection Pooling**: Configurable pool size for database connections
4. **Pagination**: Efficient offset-based pagination with configurable limits
5. **Async I/O**: Non-blocking database operations

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/employee_directory` |
| `DATABASE_POOL_SIZE` | Connection pool size | `20` |
| `SECRET_KEY` | JWT secret key | Required |
| `RATE_LIMIT_REQUESTS` | Requests per window | `100` |
| `RATE_LIMIT_WINDOW_SECONDS` | Rate limit window | `60` |
| `DEFAULT_PAGE_SIZE` | Default pagination size | `50` |
| `MAX_PAGE_SIZE` | Maximum pagination size | `1000` |

## Development

```bash
# Run with hot reload
uvicorn app.main:app --reload --port 8000

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## License

MIT
