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
- Khởi động PostgreSQL 16
- Chạy database migrations
- Seed dữ liệu mẫu
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
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/employee_directory
```

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

## Sử dụng API

### Header bắt buộc

Tất cả requests đến `/api/v1/employees/search` cần có header:
```
X-Organization-ID: <organization_id>
```

### Ví dụ Search API

**Tìm tất cả employees (không bao gồm terminated):**
```bash
curl -X GET "http://localhost:8000/api/v1/employees/search" \
  -H "X-Organization-ID: 1"
```

**Tìm với filters:**
```bash
curl -X GET "http://localhost:8000/api/v1/employees/search?status=Active&department=Engineering&page=1&page_size=20" \
  -H "X-Organization-ID: 1"
```

**Bao gồm terminated employees:**
```bash
curl -X GET "http://localhost:8000/api/v1/employees/search?include_terminated=true" \
  -H "X-Organization-ID: 1"
```

**Multiple status selection:**
```bash
curl -X GET "http://localhost:8000/api/v1/employees/search?status=Active&status=Not%20started" \
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
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
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
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── main.py           # FastAPI application
│   ├── config.py         # Settings
│   ├── database.py       # Database connection
│   └── seed_data.py      # Seed script
├── alembic/              # Database migrations
├── tests/                # Unit tests
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Dữ liệu mẫu

Sau khi seed, hệ thống sẽ có:

| Organization ID | Tên | Visible Columns |
|----------------|-----|-----------------|
| 1 | TechCorp International | Tất cả columns |
| 2 | HealthFirst Medical | Không có phone, location, company |
| 3 | EduLearn Academy | Chỉ basic info |

Mỗi organization có 50-150 employees ngẫu nhiên.

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
