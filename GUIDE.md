# Huong Dan Chay Du An Employee Search Service

## Yeu Cau He Thong

- Docker & Docker Compose
- Python 3.11+ (neu chay local)
- PostgreSQL 16+ (neu chay local)

---

## Cach 1: Chay voi Docker (Khuyen nghi)

### Buoc 1: Clone repository

```bash
git clone https://github.com/Unknown9421/interview-fastapi-employee-directory.git
cd interview-fastapi-employee-directory
```

### Buoc 2: Khoi dong services

```bash
docker-compose up --build
```

Lenh nay se:
- Build Docker image cho ung dung
- Khoi dong PostgreSQL 16 (port 5436)
- Auto-generate database migrations tu SQLAlchemy models
- Seed **10,000 employees** ngau nhien
- Khoi dong FastAPI server (port 8000)

### Buoc 3: Truy cap API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Dung services

```bash
docker-compose down
```

De xoa ca database volume:
```bash
docker-compose down -v
```

---

## Cach 2: Chay Local (Development)

### Buoc 1: Tao virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoac
venv\Scripts\activate  # Windows
```

### Buoc 2: Cai dat dependencies

```bash
pip install -r requirements.txt
```

### Buoc 3: Cau hinh database

Tao file `.env` tu template:
```bash
cp .env.example .env
```

Chinh sua `.env` voi thong tin database:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5436/employee_directory
```

### Buoc 4: Tao database

```bash
psql -U postgres -c "CREATE DATABASE employee_directory;"
```

### Buoc 5: Chay migrations

```bash
alembic upgrade head
```

### Buoc 6: Seed du lieu mau

```bash
python -m app.seed_data
```

### Buoc 7: Khoi dong server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Su Dung API

### Header bat buoc

Tat ca requests den `/api/v1/employees` can co header:
```
X-Organization-ID: <organization_id>
```

### Vi du API

**Lay danh sach employees:**
```bash
curl -X GET "http://localhost:8000/api/v1/employees" \
  -H "X-Organization-ID: 1"
```

**Voi filters:**
```bash
curl -X GET "http://localhost:8000/api/v1/employees?status=Active&department=Engineering" \
  -H "X-Organization-ID: 1"
```

**Bao gom terminated employees:**
```bash
curl -X GET "http://localhost:8000/api/v1/employees?include_terminated=true" \
  -H "X-Organization-ID: 1"
```

**Multi-select filters:**
```bash
curl -X GET "http://localhost:8000/api/v1/employees?department=Engineering&department=Marketing" \
  -H "X-Organization-ID: 1"
```

**Tim kiem:**
```bash
curl -X GET "http://localhost:8000/api/v1/employees?search=john" \
  -H "X-Organization-ID: 1"
```

**Lay filter options:**
```bash
curl -X GET "http://localhost:8000/api/v1/employees/filters" \
  -H "X-Organization-ID: 1"
```

---

## Chay Tests

### Voi Docker

```bash
docker-compose exec app pytest -v
```

### Local

```bash
pytest -v
```

### Voi coverage report

```bash
pytest --cov=app --cov-report=term-missing
```

---

## Shell Scripts

| Script | Mo ta | Su dung |
|--------|-------|---------|
| `init-db.sh` | Khoi tao database | `./scripts/init-db.sh` |
| `start.sh` | Khoi dong app | `./scripts/start.sh` |
| `migrate.sh` | Migration commands | `./scripts/migrate.sh [command]` |
| `test.sh` | Chay tests | `./scripts/test.sh` |
| `dev.sh` | Development server | `./scripts/dev.sh` |

### Migration Commands

```bash
./scripts/migrate.sh create "migration_name"  # Tao migration moi
./scripts/migrate.sh upgrade                  # Apply migrations
./scripts/migrate.sh downgrade                # Rollback migration
./scripts/migrate.sh reset                    # Reset database
./scripts/migrate.sh history                  # Xem lich su
./scripts/migrate.sh current                  # Xem revision hien tai
```

---

## Du Lieu Mau

Sau khi seed, he thong co **10,000 employees**:

| Organization ID | Ten | Visible Columns | ~Employees |
|----------------|-----|-----------------|------------|
| 1 | TechCorp International | Tat ca columns | ~5,000 |
| 2 | HealthFirst Medical | Khong co phone, location, company | ~3,000 |
| 3 | EduLearn Academy | Chi basic info | ~2,000 |

**Distribution:** 70% Active, 20% Not started, 10% Terminated

---

## Rate Limiting

- **100 requests / 60 giay**
- Response headers:
  - `X-RateLimit-Limit`: Gioi han toi da
  - `X-RateLimit-Remaining`: So requests con lai
  - `X-RateLimit-Window`: Thoi gian window

Vuot qua gioi han tra ve `429 Too Many Requests`.

---

## Troubleshooting

### Loi ket noi database

```
sqlalchemy.exc.OperationalError: connection refused
```

**Giai phap**: Dam bao PostgreSQL dang chay va DATABASE_URL dung.

### Loi migration

```bash
alembic downgrade base
alembic upgrade head
```

### Xoa toan bo data

```bash
docker-compose down -v
docker-compose up --build
```

---

## Repository Pattern

### Kien truc 3-Layer

Du an nay su dung **3-Layer Architecture** voi **Repository Pattern**:

```
app/
├── api/              # Presentation Layer - API endpoints
├── services/         # Service Layer - Business logic
├── repositories/     # Repository Layer - Database queries
├── models/           # ORM entities
└── schemas/          # DTOs (Pydantic)
```

### Cau truc Repository

```
app/repositories/
├── __init__.py                      # Exports
├── base.py                          # Generic CRUD operations
├── employee_repository.py           # Employee-specific queries
└── organization_repository.py       # Organization-specific queries
```

### Cach su dung Repository

**1. Trong Service Layer:**

```python
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.organization_repository import OrganizationRepository

class EmployeeService:
    def __init__(
        self,
        employee_repo: EmployeeRepository,
        org_repo: OrganizationRepository
    ):
        self.employee_repo = employee_repo
        self.org_repo = org_repo

    async def get_employee(self, employee_id: int):
        # Goi repository method thay vi viet SQL truc tiep
        return await self.employee_repo.get_by_id(employee_id)

    async def search_employees(self, org_id: int, filters: dict):
        # Repository xu ly tat ca SQL logic
        employees, total = await self.employee_repo.find_by_organization(
            org_id, filters, page=1, page_size=20
        )
        return employees, total
```

**2. Trong API Endpoints (qua Dependency Injection):**

```python
from fastapi import APIRouter, Depends
from app.services.employee_service import EmployeeService
from app.core.dependencies import get_employee_service

router = APIRouter()

@router.get("/employees/{id}")
async def get_employee(
    id: int,
    service: EmployeeService = Depends(get_employee_service)
):
    # Service tu dong nhan repositories qua DI
    employee = await service.get_employee(id)
    return employee
```

**3. Tao Repository moi cho Entity khac:**

```python
from app.repositories.base import BaseRepository
from app.models.department import Department

class DepartmentRepository(BaseRepository[Department]):
    """Repository cho Department entity."""

    def __init__(self, db: AsyncSession):
        super().__init__(Department, db)

    # Them methods dac thu cho Department
    async def find_by_name(self, name: str):
        return await self.find_one(Department.name == name)
```

### Loi ich cua Repository Pattern

✅ **Separation of Concerns**: Service chi chua business logic
✅ **Testability**: De dang mock repositories cho unit tests
✅ **Maintainability**: Doi database khong anh huong business logic
✅ **Code Reusability**: BaseRepository giam code lap lai
✅ **SOLID Principles**: Tuan thu SRP, DIP, OCP

### Vi du Query phuc tap

**Truoc khi co Repository (BAD):**
```python
# Service truc tiep viet SQL - Sai!
class EmployeeService:
    async def search_employees(self, org_id):
        result = await self.db.execute(
            select(Employee).where(Employee.organization_id == org_id)
        )
        return result.scalars().all()
```

**Sau khi co Repository (GOOD):**
```python
# Service chi goi repository method - Dung!
class EmployeeService:
    async def search_employees(self, org_id):
        return await self.employee_repo.find_by_organization(org_id, {})
```
