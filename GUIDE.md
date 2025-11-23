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
