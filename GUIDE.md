# Hướng dẫn chạy dự án Employee Search Service

## Yêu cầu hệ thống

- Docker & Docker Compose
- Python 3.10+ (nếu chạy local)
- PostgreSQL 16+ (nếu chạy local)

---

## Cách 1: Chạy với Docker (Khuyến nghị)

### Bước 1: Clone repository

```bash
git clone https://github.com/Unknown9421/interview-fastapi-employee-directory.git
cd interview-fastapi-employee-directory
```

### Bước 2: Khởi động services

```bash
docker-compose up --build
```

Lệnh này sẽ:
- Build Docker image cho ứng dụng
- Khởi động PostgreSQL 16 (port 5436)
- Chạy database migrations
- Seed **10,000 employees** ngẫu nhiên
- Khởi động FastAPI server

### Bước 3: Truy cập API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Dừng services

```bash
docker-compose down
```

Để xóa cả database volume:
```bash
docker-compose down -v
```

---

## Cách 2: Chạy Local (Development)

### Bước 1: Tạo virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate  # Windows
```

### Bước 2: Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### Bước 3: Cấu hình database

Tạo file `.env` từ template:
```bash
cp .env.example .env
```

Chỉnh sửa `.env` với thông tin database của bạn:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5436/employee_directory
```

> **Lưu ý**: Port mặc định là 5436 để tránh xung đột với PostgreSQL local.

### Bước 4: Tạo database

```bash
# Kết nối PostgreSQL và tạo database
psql -U postgres -c "CREATE DATABASE employee_directory;"
```

### Bước 5: Chạy migrations

```bash
alembic upgrade head
```

### Bước 6: Seed dữ liệu mẫu

```bash
python -m app.seed_data
```

### Bước 7: Khởi động server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Shell Scripts (Mini CI/CD)

Project bao gồm các helper scripts trong thư mục `scripts/`:

| Script | Mô tả | Sử dụng |
|--------|-------|---------|
| `init-db.sh` | Khởi tạo database (migrations + seed) | `./scripts/init-db.sh` |
| `start.sh` | Khởi động app với auto-initialization | `./scripts/start.sh` |
| `migrate.sh` | Helper cho migration commands | `./scripts/migrate.sh [command]` |
| `test.sh` | Chạy tests với coverage | `./scripts/test.sh` |
| `dev.sh` | Development server với auto-reload | `./scripts/dev.sh` |

### Migration Commands

```bash
./scripts/migrate.sh create "migration_name"  # Tạo migration mới
./scripts/migrate.sh upgrade                  # Apply tất cả migrations
./scripts/migrate.sh downgrade                # Rollback migration cuối
./scripts/migrate.sh reset                    # Reset database
./scripts/migrate.sh history                  # Xem lịch sử migrations
./scripts/migrate.sh current                  # Xem revision hiện tại
```

---

## Sử dụng API

### Header bắt buộc

Tất cả requests đến `/api/v1/employees` cần có header:
```
X-Organization-ID: <organization_id>
```

### Ví dụ API

**Lấy danh sách employees (không bao gồm terminated):**
```bash
curl -X GET "http://localhost:8000/api/v1/employees" \
  -H "X-Organization-ID: 1"
```

**Lấy với filters:**
```bash
curl -X GET "http://localhost:8000/api/v1/employees?status=Active&department=Engineering&page=1&page_size=20" \
  -H "X-Organization-ID: 1"
```

**Bao gồm terminated employees:**
```bash
curl -X GET "http://localhost:8000/api/v1/employees?include_terminated=true" \
  -H "X-Organization-ID: 1"
```

**Multiple status selection:**
```bash
curl -X GET "http://localhost:8000/api/v1/employees?status=Active&status=Not%20started" \
  -H "X-Organization-ID: 1"
```

**Multi-select filters (location, department, etc.):**
```bash
curl -X GET "http://localhost:8000/api/v1/employees?department=Engineering&department=Marketing&location=New%20York" \
  -H "X-Organization-ID: 1"
```

**Nhảy trang (Page jumping):**
```bash
curl -X GET "http://localhost:8000/api/v1/employees?page=5&page_size=50" \
  -H "X-Organization-ID: 1"
```

**Lấy filter options cho dropdowns:**
```bash
curl -X GET "http://localhost:8000/api/v1/employees/filters" \
  -H "X-Organization-ID: 1"
```

### Response mẫu

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

## Chạy Tests

### Với Docker

```bash
docker-compose exec app pytest
```

### Local

```bash
pytest
```

### Với coverage report

```bash
pytest --cov=app --cov-report=html
```

---

## Cấu trúc dự án

```
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Dependencies
│   ├── middleware/       # Rate limiter
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas (DTOs)
│   ├── services/         # Business logic
│   ├── main.py           # FastAPI application
│   ├── config.py         # Settings
│   ├── database.py       # Database connection
│   └── seed_data.py      # Seed script (10,000 records)
├── alembic/              # Database migrations
├── scripts/              # Shell scripts (CI/CD)
│   ├── init-db.sh        # Database initialization
│   ├── start.sh          # Application startup
│   ├── migrate.sh        # Migration helper
│   ├── test.sh           # Test runner
│   └── dev.sh            # Development server
├── tests/                # Unit tests
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Dữ liệu mẫu

Sau khi seed, hệ thống sẽ có **10,000 employees** phân bố như sau:

| Organization ID | Tên | Visible Columns | ~Employees |
|----------------|-----|-----------------|------------|
| 1 | TechCorp International | Tất cả columns | ~5,000 (50%) |
| 2 | HealthFirst Medical | Không có phone, location, company | ~3,000 (30%) |
| 3 | EduLearn Academy | Chỉ basic info | ~2,000 (20%) |

**Distribution:**
- 70% Active, 20% Not started, 10% Terminated
- Dữ liệu được insert theo batch (500 records/batch) để tối ưu performance

---

## Rate Limiting

API có rate limiting:
- **100 requests / 60 giây** (mặc định)
- Headers trong response:
  - `X-RateLimit-Limit`: Giới hạn tối đa
  - `X-RateLimit-Remaining`: Số requests còn lại
  - `X-RateLimit-Window`: Thời gian window (giây)

Khi vượt quá giới hạn, API trả về `429 Too Many Requests`.

---

## Troubleshooting

### Lỗi kết nối database

```
sqlalchemy.exc.OperationalError: connection refused
```

**Giải pháp**: Đảm bảo PostgreSQL đang chạy và DATABASE_URL đúng.

### Lỗi migration

```bash
# Reset migrations
alembic downgrade base
alembic upgrade head
```

### Xóa toàn bộ data và bắt đầu lại

```bash
docker-compose down -v
docker-compose up --build
```

---

## PyCharm Configuration

1. Mở project trong PyCharm
2. Configure Python Interpreter: `Settings > Project > Python Interpreter`
3. Add Docker Compose interpreter hoặc local venv
4. Run Configuration:
   - Script: `uvicorn`
   - Parameters: `app.main:app --reload`
   - Working directory: Project root
