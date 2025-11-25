# PHÂN TÍCH VÀ PLAN TRIỂN KHAI REPOSITORY PATTERN LAYER

---

## 📊 I. PHÂN TÍCH KIẾN TRÚC HIỆN TẠI

### 1.1. Cấu trúc hiện tại (2-Layer Architecture)

```
┌──────────────────────────────────────┐
│   Presentation Layer (API/Router)   │  ← app/api/employees.py
│  - Định nghĩa endpoints              │
│  - Validation qua Pydantic           │
│  - HTTP Request/Response handling    │
└────────────────┬─────────────────────┘
                 │ Depends(get_employee_service)
                 ↓
┌──────────────────────────────────────┐
│      Service Layer (Business)        │  ← app/services/employee_service.py
│  - Business logic                    │
│  - ❌ DATABASE QUERIES (SQLAlchemy)  │  ← VẤN ĐỀ!
│  - Filter logic, Pagination          │
│  - Column filtering                  │
└────────────────┬─────────────────────┘
                 │ self.db.execute(select(...))
                 ↓
┌──────────────────────────────────────┐
│         Database (PostgreSQL)        │
│  - SQLAlchemy ORM Models             │
│  - Tables: employees, organizations  │
└──────────────────────────────────────┘
```

### 1.2. Files hiện tại

| Layer | Files | Trách nhiệm |
|-------|-------|-------------|
| **Presentation** | `app/api/employees.py` (165 LOC) | - Định nghĩa 2 endpoints: GET /filters, GET /<br>- Inject `EmployeeService` qua Depends<br>- Convert Entity → DTO |
| **Service** | `app/services/employee_service.py` (202 LOC) | - **❌ Chứa 28 SQL queries trực tiếp**<br>- Methods: `search_employees()`, `get_organization_config()`, `validate_organization()`, `get_filter_options()`<br>- Deferred Join pagination logic |
| **Models** | `app/models/employee.py` (55 LOC)<br>`app/models/organization.py` (37 LOC)<br>`app/models/base.py` (113 LOC) | - SQLAlchemy ORM definitions<br>- Mixins: TimestampMixin, AuditMixin, SoftDeleteMixin |
| **Schemas** | `app/schemas/employee.py` (73 LOC) | - Pydantic DTOs: `EmployeeCreateDTO`, `EmployeeResponseDTO`, `PaginatedResponseDTO` |
| **Dependencies** | `app/core/dependencies.py` (25 LOC) | - `get_db()`: Database session factory<br>- `get_employee_service()`: Service factory<br>- `get_organization_id()`: Extract org ID from header |

---

## 🚨 II. VẤN ĐỀ HIỆN TẠI (Violations)

### 2.1. Vi phạm Separation of Concerns (SoC)

**Service Layer đang làm quá nhiều việc:**

```python
# ❌ BAD: Service trực tiếp viết SQL queries
class EmployeeService:
    async def search_employees(self, ...):
        # Service KHÔNG NÊN biết về SQLAlchemy!
        result = await self.db.execute(
            select(Employee)
            .where(Employee.organization_id == organization_id)
            .order_by(Employee.id)
        )
```

**Hậu quả:**
- Service bị **tight coupling** với Database (biết quá nhiều về SQLAlchemy ORM)
- Khó **test** vì không thể mock database layer dễ dàng
- Khó **maintain** khi cần đổi ORM hoặc database engine
- Vi phạm **Dependency Inversion Principle (DIP)**: Service (high-level) phụ thuộc Database (low-level)

### 2.2. Vi phạm Single Responsibility Principle (SRP)

**`EmployeeService` có quá nhiều trách nhiệm:**
1. ✅ Business logic (validate organization, filter columns) → **Đúng**
2. ❌ Database access logic (viết queries, execute) → **SAI** (nên tách ra Repository)
3. ✅ Orchestration (gọi nhiều repository methods) → **Đúng**

**Số lượng SQL queries trong Service:**
- `get_organization_config()`: 1 query
- `validate_organization()`: 1 query
- `get_filter_options()`: 4 queries (locations, companies, departments, positions)
- `search_employees()`: 2 queries (count + deferred join)
- **Tổng: 8 phương thức → 28 dòng SQL code trong Service ❌**

### 2.3. Khó mở rộng (Scalability Issues)

**Khi cần thêm entity mới (ví dụ: `Department`, `Position`):**
- Phải viết lại toàn bộ SQL logic trong Service mới
- Duplicate code (CRUD operations giống nhau cho mọi entity)
- Không có **Generic Repository** để tái sử dụng

---

## ✅ III. GIẢI PHÁP: REPOSITORY PATTERN LAYER

### 3.1. Kiến trúc mới (3-Layer Architecture + Repository Pattern)

```
┌──────────────────────────────────────┐
│   Presentation Layer (API/Router)   │  ← app/api/employees.py (NO CHANGE*)
│  - Định nghĩa endpoints              │
│  - Validation qua Pydantic           │
└────────────────┬─────────────────────┘
                 │ Depends(get_employee_service)
                 ↓
┌──────────────────────────────────────┐
│      Service Layer (Business)        │  ← app/services/employee_service.py (REFACTOR)
│  ✅ ONLY Business logic               │
│  ✅ Orchestration (gọi repo methods) │
│  ❌ NO DATABASE QUERIES               │
└────────────────┬─────────────────────┘
                 │ self.employee_repo.find_by_organization(...)
                 ↓
┌──────────────────────────────────────┐
│   🆕 Repository Layer (Data Access)  │  ← app/repositories/ (NEW!)
│  ✅ Generic Base Repository           │  ← base.py
│  ✅ EmployeeRepository                │  ← employee_repository.py
│  ✅ OrganizationRepository            │  ← organization_repository.py
│  ✅ TẤT CẢ SQL queries ở đây          │
└────────────────┬─────────────────────┘
                 │ session.execute(select(...))
                 ↓
┌──────────────────────────────────────┐
│         Database (PostgreSQL)        │
│  - Models (NO CHANGE)                │
└──────────────────────────────────────┘
```

*Note: API có thể có minor changes trong DI (inject repository)

### 3.2. Nguyên tắc thiết kế Repository Pattern

#### A. Generic Repository (Base Class)

**Mục đích:** Tái sử dụng code cho CRUD operations chung

```python
# app/repositories/base.py
from typing import TypeVar, Generic, Type, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

T = TypeVar("T")  # Generic Type (Employee, Organization, etc.)

class BaseRepository(Generic[T]):
    """
    Generic Repository cung cấp CRUD operations cơ bản.
    Mọi Repository cụ thể sẽ kế thừa từ class này.
    """
    def __init__(self, model: Type[T], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: int) -> Optional[T]:
        """Get single record by ID."""
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all records with pagination."""
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> T:
        """Create new record."""
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(self, id: int, **kwargs) -> Optional[T]:
        """Update existing record."""
        instance = await self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            await self.db.flush()
            await self.db.refresh(instance)
        return instance

    async def delete(self, id: int) -> bool:
        """Hard delete record."""
        instance = await self.get_by_id(id)
        if instance:
            await self.db.delete(instance)
            await self.db.flush()
            return True
        return False

    async def count(self) -> int:
        """Count total records."""
        result = await self.db.execute(select(func.count(self.model.id)))
        return result.scalar()
```

#### B. Specific Repository (Employee)

**Mục đích:** Thêm các queries đặc thù cho Employee

```python
# app/repositories/employee_repository.py
from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.employee import Employee, EmployeeStatus

class EmployeeRepository(BaseRepository[Employee]):
    """Repository chuyên biệt cho Employee với các queries phức tạp."""

    def __init__(self, db: AsyncSession):
        super().__init__(Employee, db)

    # ===== QUERIES ĐẶC THÙ CHO EMPLOYEE =====

    async def find_by_organization(
        self,
        organization_id: int,
        filters: dict,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Employee], int]:
        """
        Search employees với Deferred Join pagination.
        Đây là method PHỨC TẠP nhất, di chuyển từ Service sang đây.
        """
        conditions = self._build_search_conditions(organization_id, filters)

        # Step 1: Count total
        total = await self._count_with_conditions(conditions)

        # Step 2: Deferred Join - Get IDs only
        offset = (page - 1) * page_size
        id_subquery = (
            select(Employee.id)
            .where(*conditions)
            .order_by(Employee.id)
            .limit(page_size)
            .offset(offset)
        ).subquery()

        # Step 3: JOIN back to get full data
        query = (
            select(Employee)
            .join(id_subquery, Employee.id == id_subquery.c.id)
            .order_by(Employee.id)
        )

        result = await self.db.execute(query)
        employees = list(result.scalars().all())

        return employees, total

    async def get_distinct_values(
        self,
        organization_id: int,
        column_name: str
    ) -> List[str]:
        """
        Get distinct values cho filter dropdowns.
        Dùng cho locations, companies, departments, positions.
        """
        column = getattr(Employee, column_name)
        result = await self.db.execute(
            select(distinct(column))
            .where(Employee.organization_id == organization_id)
            .where(Employee.is_deleted == False)
            .where(column.isnot(None))
            .order_by(column)
        )
        return [row[0] for row in result.fetchall()]

    async def exists_by_organization(self, organization_id: int) -> bool:
        """Check if organization has any employees."""
        result = await self.db.execute(
            select(func.count(Employee.id))
            .where(Employee.organization_id == organization_id)
        )
        return result.scalar() > 0

    # ===== PRIVATE HELPERS =====

    def _build_search_conditions(self, organization_id: int, filters: dict) -> list:
        """Build WHERE conditions từ filters."""
        conditions = [
            Employee.organization_id == organization_id,
            Employee.is_deleted == False,
        ]

        # Text search
        if q := filters.get("q"):
            search_term = f"%{q}%"
            conditions.append(
                or_(
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.email.ilike(search_term),
                )
            )

        # Status filter
        if status := filters.get("status"):
            conditions.append(Employee.status.in_(status))

        # Multi-select filters
        for field in ["locations", "companies", "departments", "positions"]:
            if values := filters.get(field):
                column = getattr(Employee, field[:-1])  # remove 's'
                conditions.append(column.in_(values))

        return conditions

    async def _count_with_conditions(self, conditions: list) -> int:
        """Count records with WHERE conditions."""
        result = await self.db.execute(
            select(func.count(Employee.id)).where(*conditions)
        )
        return result.scalar()
```

#### C. Organization Repository

```python
# app/repositories/organization_repository.py
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.organization import Organization, OrganizationConfig

class OrganizationRepository(BaseRepository[Organization]):
    """Repository for Organization entity."""

    def __init__(self, db: AsyncSession):
        super().__init__(Organization, db)

    async def get_active_by_id(self, org_id: int) -> Optional[Organization]:
        """Get active organization by ID."""
        result = await self.db.execute(
            select(Organization)
            .where(Organization.id == org_id)
            .where(Organization.is_active == True)
        )
        return result.scalar_one_or_none()

    async def get_visible_columns(self, org_id: int) -> Optional[List[str]]:
        """Get visible columns config for organization."""
        result = await self.db.execute(
            select(OrganizationConfig.visible_columns)
            .where(OrganizationConfig.organization_id == org_id)
        )
        return result.scalar_one_or_none()

    async def exists_and_active(self, org_id: int) -> bool:
        """Check if organization exists and is active."""
        result = await self.db.execute(
            select(Organization.id)
            .where(Organization.id == org_id)
            .where(Organization.is_active == True)
        )
        return result.scalar_one_or_none() is not None
```

### 3.3. Dependency Injection Pattern

**Cơ chế hoạt động:**

```python
# app/core/dependencies.py (CẦN REFACTOR)

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.database import get_db
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.organization_repository import OrganizationRepository
from app.services.employee_service import EmployeeService

# ===== Repository Factories =====

def get_employee_repository(
    db: AsyncSession = Depends(get_db)
) -> EmployeeRepository:
    """Factory để inject EmployeeRepository."""
    return EmployeeRepository(db)

def get_organization_repository(
    db: AsyncSession = Depends(get_db)
) -> OrganizationRepository:
    """Factory để inject OrganizationRepository."""
    return OrganizationRepository(db)

# ===== Service Factory (REFACTORED) =====

def get_employee_service(
    employee_repo: EmployeeRepository = Depends(get_employee_repository),
    org_repo: OrganizationRepository = Depends(get_organization_repository),
) -> EmployeeService:
    """
    Factory để inject EmployeeService với repositories.
    Service KHÔNG còn nhận db session trực tiếp!
    """
    return EmployeeService(
        employee_repo=employee_repo,
        org_repo=org_repo
    )
```

**Luồng Dependency Injection:**

```
get_db()
  ↓
get_employee_repository(db) → EmployeeRepository instance
  ↓
get_organization_repository(db) → OrganizationRepository instance
  ↓
get_employee_service(employee_repo, org_repo) → EmployeeService instance
  ↓
API Endpoint nhận EmployeeService
```

---

## 🔧 IV. IMPACT ANALYSIS (Files bị ảnh hưởng)

### 4.1. Files CẦN TẠO MỚI (New Files)

| File Path | LOC (dự kiến) | Mô tả |
|-----------|---------------|-------|
| `app/repositories/__init__.py` | 10 | Export các repositories |
| `app/repositories/base.py` | 150 | Generic BaseRepository với CRUD methods |
| `app/repositories/employee_repository.py` | 200 | EmployeeRepository với queries đặc thù |
| `app/repositories/organization_repository.py` | 80 | OrganizationRepository |
| **TỔNG** | **440 LOC** | **4 files mới** |

### 4.2. Files CẦN REFACTOR (Major Changes)

#### A. `app/services/employee_service.py` (202 LOC → ~120 LOC)

**❌ XÓA (82 LOC):**
- Tất cả SQL queries (28 dòng `await self.db.execute(select(...))`)
- Helper method `_build_search_conditions()` → Di chuyển sang Repository
- `self.db: AsyncSession` → Thay bằng repositories

**✅ GIỮ LẠI (120 LOC):**
- Business logic: `filter_employee_columns()` (18 LOC)
- Orchestration logic (gọi nhiều repo methods)

**🔄 THAY ĐỔI:**

```python
# ❌ BEFORE (OLD)
class EmployeeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_employees(self, ...):
        # 50 lines of SQL queries here ❌
        result = await self.db.execute(select(...))

# ✅ AFTER (NEW)
class EmployeeService:
    def __init__(
        self,
        employee_repo: EmployeeRepository,
        org_repo: OrganizationRepository
    ):
        self.employee_repo = employee_repo
        self.org_repo = org_repo

    async def search_employees(self, ...):
        # Chỉ gọi repository methods ✅
        employees, total = await self.employee_repo.find_by_organization(
            organization_id, filters, page, page_size
        )
        return employees, total
```

**Các methods cần refactor:**

| Method trong Service | Thay đổi | Repository method tương ứng |
|----------------------|----------|----------------------------|
| `get_organization_config()` | Đổi `self.db.execute(...)` thành `self.org_repo.get_visible_columns()` | `OrganizationRepository.get_visible_columns()` |
| `validate_organization()` | Đổi thành `self.org_repo.exists_and_active()` | `OrganizationRepository.exists_and_active()` |
| `get_filter_options()` | 4 queries → 1 loop gọi `self.employee_repo.get_distinct_values()` | `EmployeeRepository.get_distinct_values()` |
| `search_employees()` | Đổi thành `self.employee_repo.find_by_organization()` | `EmployeeRepository.find_by_organization()` |
| `filter_employee_columns()` | **GIỮ NGUYÊN** (đây là business logic) | N/A |

#### B. `app/core/dependencies.py` (25 LOC → ~60 LOC)

**✅ THÊM MỚI:**
- `get_employee_repository()` factory (10 LOC)
- `get_organization_repository()` factory (10 LOC)

**🔄 REFACTOR:**
- `get_employee_service()`: Thay đổi signature, inject repositories thay vì db

```python
# ❌ BEFORE
def get_employee_service(db: AsyncSession = Depends(get_db)) -> EmployeeService:
    return EmployeeService(db)

# ✅ AFTER
def get_employee_service(
    employee_repo: EmployeeRepository = Depends(get_employee_repository),
    org_repo: OrganizationRepository = Depends(get_organization_repository),
) -> EmployeeService:
    return EmployeeService(employee_repo, org_repo)
```

#### C. `app/api/employees.py` (165 LOC → ~165 LOC)

**✅ KHÔNG THAY ĐỔI LOGIC (Minor imports only):**
- Endpoints vẫn inject `EmployeeService` qua `Depends(get_employee_service)`
- Chỉ cần update imports nếu có thay đổi module paths

**Lý do:** API layer không cần biết Service dùng Repository hay Database trực tiếp (Abstraction hoạt động!)

### 4.3. Files KHÔNG BỊ ẢNH HƯỞNG (No Changes)

| File | Lý do |
|------|-------|
| `app/models/*.py` | Models giữ nguyên, Repository chỉ sử dụng chúng |
| `app/schemas/*.py` | DTOs độc lập với data access layer |
| `app/database.py` | Database session factory giữ nguyên |
| `app/config.py` | Config không đổi |
| `app/main.py` | App initialization không đổi |
| `app/middleware/*.py` | Middleware không liên quan |
| `alembic/` | Migrations không đổi (DB schema giữ nguyên) |

---

## 📋 V. IMPLEMENTATION PLAN (Chi tiết từng bước)

### Phase 1: Preparation (Chuẩn bị - 30 phút)

#### ✅ Step 1.1: Create Repository folder structure
```bash
mkdir -p app/repositories
touch app/repositories/__init__.py
```

#### ✅ Step 1.2: Analyze existing queries
- Đọc kỹ `app/services/employee_service.py`
- List tất cả SQL queries cần di chuyển
- Xác định dependencies giữa queries

---

### Phase 2: Implement Base Repository (1 giờ)

#### ✅ Step 2.1: Create `app/repositories/base.py`

**Checklist:**
- [ ] Import Generic, TypeVar từ typing
- [ ] Implement `BaseRepository[T]` class
- [ ] Methods:
  - [ ] `get_by_id(id) → Optional[T]`
  - [ ] `get_all(skip, limit) → List[T]`
  - [ ] `create(**kwargs) → T`
  - [ ] `update(id, **kwargs) → Optional[T]`
  - [ ] `delete(id) → bool`
  - [ ] `soft_delete(id) → bool` (cho models có SoftDeleteMixin)
  - [ ] `count() → int`
  - [ ] `exists(id) → bool`

**Test ngay:**
```python
# Test instantiation
from app.models.employee import Employee
repo = BaseRepository(Employee, db_session)
employee = await repo.get_by_id(1)
assert employee.first_name == "John"
```

---

### Phase 3: Implement Employee Repository (2 giờ)

#### ✅ Step 3.1: Create `app/repositories/employee_repository.py`

**Migrate queries từ Service:**

| Service Method | Repository Method | Complexity |
|----------------|-------------------|------------|
| `search_employees()` (lines 85-178) | `find_by_organization()` | ⭐⭐⭐ High |
| `get_filter_options()` (lines 33-83) | `get_distinct_values()` | ⭐⭐ Medium |
| N/A | `exists_by_organization()` | ⭐ Low |

**Checklist:**
- [ ] Implement `find_by_organization()` với:
  - [ ] `_build_search_conditions()` helper
  - [ ] `_count_with_conditions()` helper
  - [ ] Deferred Join logic (2-step query)
  - [ ] Support tất cả filters: q, status, locations, companies, departments, positions
  - [ ] Pagination (page, page_size)
- [ ] Implement `get_distinct_values()` với:
  - [ ] Dynamic column selection (getattr)
  - [ ] Filter by organization_id, is_deleted
- [ ] Implement `exists_by_organization()`

**Test coverage:**
```python
# Test search
employees, total = await repo.find_by_organization(
    organization_id=1,
    filters={"q": "john", "status": ["Active"]},
    page=1,
    page_size=20
)
assert len(employees) <= 20
assert total >= len(employees)

# Test distinct values
locations = await repo.get_distinct_values(1, "location")
assert "Ha Noi" in locations
```

---

### Phase 4: Implement Organization Repository (45 phút)

#### ✅ Step 4.1: Create `app/repositories/organization_repository.py`

**Migrate queries từ Service:**

| Service Method | Repository Method | Lines |
|----------------|-------------------|-------|
| `validate_organization()` (lines 24-31) | `exists_and_active()` | 8 |
| `get_organization_config()` (lines 15-22) | `get_visible_columns()` | 8 |

**Checklist:**
- [ ] Implement `get_active_by_id()`
- [ ] Implement `exists_and_active()`
- [ ] Implement `get_visible_columns()` (query OrganizationConfig table)

**Test:**
```python
org = await repo.get_active_by_id(1)
assert org.is_active == True

columns = await repo.get_visible_columns(1)
assert "email" in columns
```

---

### Phase 5: Update Dependencies (30 phút)

#### ✅ Step 5.1: Refactor `app/core/dependencies.py`

**Checklist:**
- [ ] Import `EmployeeRepository`, `OrganizationRepository`
- [ ] Add `get_employee_repository()` factory
- [ ] Add `get_organization_repository()` factory
- [ ] Refactor `get_employee_service()`:
  - [ ] Remove `db: AsyncSession` parameter
  - [ ] Add `employee_repo: EmployeeRepository` parameter
  - [ ] Add `org_repo: OrganizationRepository` parameter
  - [ ] Update `return EmployeeService(employee_repo, org_repo)`

**Test DI chain:**
```python
# Test trong API endpoint
async def test_endpoint(service: EmployeeService = Depends(get_employee_service)):
    assert isinstance(service.employee_repo, EmployeeRepository)
    assert isinstance(service.org_repo, OrganizationRepository)
```

---

### Phase 6: Refactor Service Layer (2 giờ)

#### ✅ Step 6.1: Refactor `app/services/employee_service.py`

**Checklist:**

**A. Update `__init__()` method:**
- [ ] Remove `self.db: AsyncSession`
- [ ] Add `self.employee_repo: EmployeeRepository`
- [ ] Add `self.org_repo: OrganizationRepository`

**B. Refactor `validate_organization()` method:**
```python
# ❌ OLD (DELETE)
async def validate_organization(self, organization_id: int) -> bool:
    result = await self.db.execute(
        select(Organization.id)
        .where(Organization.id == organization_id)
        .where(Organization.is_active == True)
    )
    return result.scalar_one_or_none() is not None

# ✅ NEW (REPLACE)
async def validate_organization(self, organization_id: int) -> bool:
    return await self.org_repo.exists_and_active(organization_id)
```

**C. Refactor `get_organization_config()` method:**
```python
# ❌ OLD (DELETE)
async def get_organization_config(self, organization_id: int) -> Optional[list[str]]:
    result = await self.db.execute(
        select(OrganizationConfig.visible_columns)
        .where(OrganizationConfig.organization_id == organization_id)
    )
    config = result.scalar_one_or_none()
    return config if config else None

# ✅ NEW (REPLACE)
async def get_organization_config(self, organization_id: int) -> Optional[list[str]]:
    return await self.org_repo.get_visible_columns(organization_id)
```

**D. Refactor `get_filter_options()` method:**
```python
# ❌ OLD (DELETE 50 lines of duplicated queries)

# ✅ NEW (REPLACE with loop)
async def get_filter_options(self, organization_id: int) -> dict[str, list[str]]:
    filter_fields = ["location", "company", "department", "position"]

    options = {}
    for field in filter_fields:
        options[f"{field}s"] = await self.employee_repo.get_distinct_values(
            organization_id, field
        )

    return options
```

**E. Refactor `search_employees()` method:**
```python
# ❌ OLD (DELETE 90 lines)

# ✅ NEW (REPLACE)
async def search_employees(
    self,
    organization_id: int,
    q: Optional[str] = None,
    status: Optional[list[str]] = None,
    locations: Optional[list[str]] = None,
    companies: Optional[list[str]] = None,
    departments: Optional[list[str]] = None,
    positions: Optional[list[str]] = None,
    include_terminated: bool = False,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Employee], int]:
    # Build filters dict
    filters = {
        "q": q,
        "status": status,
        "locations": locations,
        "companies": companies,
        "departments": departments,
        "positions": positions,
        "include_terminated": include_terminated,
    }

    # Delegate to repository
    return await self.employee_repo.find_by_organization(
        organization_id, filters, page, page_size
    )
```

**F. Keep `filter_employee_columns()` unchanged:**
- [ ] Giữ nguyên method này (business logic, không phải data access)

**Test toàn bộ Service:**
```python
service = EmployeeService(employee_repo, org_repo)

# Test validate
assert await service.validate_organization(1) == True

# Test get config
config = await service.get_organization_config(1)
assert "email" in config

# Test search
employees, total = await service.search_employees(organization_id=1)
assert total > 0
```

---

### Phase 7: Update `__init__.py` exports (15 phút)

#### ✅ Step 7.1: Update `app/repositories/__init__.py`

```python
from app.repositories.base import BaseRepository
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.organization_repository import OrganizationRepository

__all__ = [
    "BaseRepository",
    "EmployeeRepository",
    "OrganizationRepository",
]
```

---

### Phase 8: Testing (1 giờ)

#### ✅ Step 8.1: Unit Tests cho Repositories

**Create `tests/repositories/test_employee_repository.py`:**
```python
import pytest
from app.repositories.employee_repository import EmployeeRepository

@pytest.mark.asyncio
async def test_find_by_organization(db_session, seed_employees):
    repo = EmployeeRepository(db_session)
    employees, total = await repo.find_by_organization(
        organization_id=1,
        filters={},
        page=1,
        page_size=10
    )
    assert len(employees) <= 10
    assert total > 0

@pytest.mark.asyncio
async def test_get_distinct_values(db_session, seed_employees):
    repo = EmployeeRepository(db_session)
    locations = await repo.get_distinct_values(1, "location")
    assert len(locations) > 0
```

#### ✅ Step 8.2: Integration Tests cho Service

```python
@pytest.mark.asyncio
async def test_employee_service_with_repositories(db_session):
    employee_repo = EmployeeRepository(db_session)
    org_repo = OrganizationRepository(db_session)
    service = EmployeeService(employee_repo, org_repo)

    employees, total = await service.search_employees(organization_id=1)
    assert total > 0
```

#### ✅ Step 8.3: API Tests (E2E)

```python
def test_list_employees_endpoint(client):
    response = client.get(
        "/api/v1/employees",
        headers={"X-Organization-ID": "1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "pagination" in data
```

---

### Phase 9: Documentation Updates (45 phút)

#### ✅ Step 9.1: Update `README.md`

**Thêm section:**

```markdown
## 🏗️ Architecture

This project follows **3-Layer Architecture** with **Repository Pattern**:

### Layers:

1. **Presentation Layer** (`app/api/`)
   - REST API endpoints
   - Request/Response handling
   - Input validation via Pydantic

2. **Service Layer** (`app/services/`)
   - Business logic
   - Orchestration (calling multiple repositories)
   - Data transformation

3. **Repository Layer** (`app/repositories/`)
   - Data access abstraction
   - All database queries
   - CRUD operations

4. **Models Layer** (`app/models/`)
   - SQLAlchemy ORM models
   - Database schema definitions

### Benefits:

- ✅ **Separation of Concerns**: Each layer has single responsibility
- ✅ **Testability**: Easy to mock repositories for unit tests
- ✅ **Maintainability**: Changes to database don't affect business logic
- ✅ **Reusability**: Generic repository reduces code duplication
```

#### ✅ Step 9.2: Update `GUIDE.md`

**Thêm section "Repository Pattern":**

```markdown
## Repository Pattern

### Cấu trúc Repository

```
app/repositories/
├── __init__.py
├── base.py                      # Generic CRUD operations
├── employee_repository.py       # Employee-specific queries
└── organization_repository.py   # Organization-specific queries
```

### Cách sử dụng Repository

**Trong Service:**
```python
class EmployeeService:
    def __init__(self, employee_repo: EmployeeRepository):
        self.employee_repo = employee_repo

    async def get_employee(self, id: int):
        return await self.employee_repo.get_by_id(id)
```

**Trong API (qua Dependency Injection):**
```python
@router.get("/employees/{id}")
async def get_employee(
    id: int,
    service: EmployeeService = Depends(get_employee_service)
):
    employee = await service.get_employee(id)
    return employee
```
```

#### ✅ Step 9.3: Create `ARCHITECTURE.md` (new file)

**Tạo document chi tiết về kiến trúc:**

```markdown
# Architecture Documentation

## Overview

This document describes the architecture of the Employee Search Service, which follows **3-Layer Architecture** combined with **Repository Pattern** and **SOLID principles**.

... (full architecture details from this document)
```

#### ✅ Step 9.4: Update `REQUIREMENT.MD`

**Cập nhật phần Architecture Requirements:**

```markdown
## ✅ Implemented: Repository Pattern Layer

The system now includes a dedicated Repository Layer that:
- Abstracts all database access logic
- Provides Generic CRUD operations via BaseRepository
- Implements specific queries in EmployeeRepository and OrganizationRepository
- Enables easy testing through dependency injection
- Follows Dependency Inversion Principle (DIP)
```

---

### Phase 10: Code Review & Cleanup (30 phút)

#### ✅ Step 10.1: Code Quality Checks

**Checklist:**
- [ ] All SQL queries removed from Service layer
- [ ] Type hints added to all repository methods
- [ ] Docstrings added to public methods
- [ ] No unused imports
- [ ] Consistent naming conventions
- [ ] Error handling added (try/except for database errors)

#### ✅ Step 10.2: Run linters

```bash
# Format code
black app/

# Check types
mypy app/

# Check style
flake8 app/

# Sort imports
isort app/
```

---

## 📊 VI. IMPACT SUMMARY

### 6.1. Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Total Files** | 17 | 21 | +4 files |
| **Total LOC** | ~1,200 | ~1,500 | +300 LOC |
| **Service LOC** | 202 | 120 | -82 LOC |
| **SQL queries in Service** | 28 lines | 0 lines | -28 lines ✅ |
| **Layers** | 2 (API + Service) | 3 (API + Service + Repository) | +1 layer |
| **Testability** | Medium (hard to mock DB) | High (easy to mock repos) | 🔼 Improved |
| **Code Reusability** | Low (duplicate CRUD) | High (Generic Repo) | 🔼 Improved |

### 6.2. Dependencies Graph (After Implementation)

```
API Layer (employees.py)
  ├─ Depends(get_employee_service)
  │   └─ EmployeeService
  │       ├─ employee_repo: EmployeeRepository
  │       │   ├─ BaseRepository[Employee]
  │       │   └─ db: AsyncSession
  │       └─ org_repo: OrganizationRepository
  │           ├─ BaseRepository[Organization]
  │           └─ db: AsyncSession
  └─ Depends(get_organization_id)
```

### 6.3. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Breaking existing API behavior** | Low | High | Comprehensive integration tests |
| **Performance regression** | Medium | Medium | Benchmark before/after, profile queries |
| **Merge conflicts với branch khác** | High | Low | Communicate with team, merge main first |
| **Missing test coverage** | Medium | High | Write tests for each repository method |

---

## 🎯 VII. VERIFICATION CHECKLIST

### Functional Tests

- [ ] **API Endpoints still work:**
  - [ ] `GET /api/v1/employees` returns correct data
  - [ ] `GET /api/v1/employees/filters` returns filter options
  - [ ] Pagination works (page jumping)
  - [ ] Multi-select filters work
  - [ ] Text search works
  - [ ] Organization isolation works (multi-tenancy)

- [ ] **Performance:**
  - [ ] Search query execution time < 100ms (same as before)
  - [ ] Deferred Join still works correctly
  - [ ] No N+1 query problems

- [ ] **Error Handling:**
  - [ ] Invalid organization ID returns 404
  - [ ] Database errors handled gracefully
  - [ ] Validation errors return 422

### Code Quality

- [ ] **No SQL in Service Layer:**
  - [ ] Search in `employee_service.py` for `select(` → 0 results
  - [ ] Search for `self.db.execute(` → 0 results

- [ ] **Type Hints:**
  - [ ] All repository methods have return type hints
  - [ ] All service methods have return type hints
  - [ ] `mypy app/` passes with 0 errors

- [ ] **Documentation:**
  - [ ] All public methods have docstrings
  - [ ] README.md updated
  - [ ] GUIDE.md updated
  - [ ] ARCHITECTURE.md created

- [ ] **Tests:**
  - [ ] Unit tests for BaseRepository
  - [ ] Unit tests for EmployeeRepository
  - [ ] Unit tests for OrganizationRepository
  - [ ] Integration tests for EmployeeService
  - [ ] API tests (E2E)
  - [ ] Test coverage > 80%

---

## 📝 VIII. ROLLBACK PLAN

**Nếu implementation gặp vấn đề nghiêm trọng:**

### Option 1: Git Revert (Recommended)
```bash
# Revert về commit trước khi implement Repository Pattern
git revert HEAD~5..HEAD
git push
```

### Option 2: Feature Flag
```python
# app/config.py
USE_REPOSITORY_PATTERN = os.getenv("USE_REPOSITORY_PATTERN", "false").lower() == "true"

# app/core/dependencies.py
def get_employee_service(db: AsyncSession = Depends(get_db)):
    if settings.USE_REPOSITORY_PATTERN:
        # New implementation with repositories
        return EmployeeService(employee_repo, org_repo)
    else:
        # Old implementation with direct DB access
        return EmployeeService(db)
```

---

## 🚀 IX. ESTIMATED TIMELINE

| Phase | Time | Cumulative |
|-------|------|------------|
| **Phase 1: Preparation** | 30 min | 30 min |
| **Phase 2: Base Repository** | 1 hour | 1.5 hours |
| **Phase 3: Employee Repository** | 2 hours | 3.5 hours |
| **Phase 4: Organization Repository** | 45 min | 4.25 hours |
| **Phase 5: Update Dependencies** | 30 min | 4.75 hours |
| **Phase 6: Refactor Service** | 2 hours | 6.75 hours |
| **Phase 7: Update Exports** | 15 min | 7 hours |
| **Phase 8: Testing** | 1 hour | 8 hours |
| **Phase 9: Documentation** | 45 min | 8.75 hours |
| **Phase 10: Code Review** | 30 min | 9.25 hours |
| **TOTAL** | **~9.25 hours** | **~1.5 working days** |

---

## ✅ X. NEXT STEPS

### Immediate Actions:

1. **Review this plan** với team/lead
2. **Create branch**: `git checkout -b feature/add-repository-pattern-layer`
3. **Estimate time** dựa trên team capacity
4. **Assign tasks** nếu làm team

### Implementation Order:

1. Start với **Phase 2** (BaseRepository) - Foundation
2. Implement **Phase 3** (EmployeeRepository) - Most complex
3. Quick win: **Phase 4** (OrganizationRepository)
4. Wire up: **Phase 5** (Dependencies)
5. Refactor: **Phase 6** (Service)
6. Verify: **Phase 8** (Testing)
7. Document: **Phase 9** (Docs)

---

## 📚 XI. REFERENCES

### Internal Documents:
- [FastAPI 3-Layer Architecture Guide](./docs/architecture.md) (User-provided)
- [SOLID Principles](./docs/solid-principles.md)

### External Resources:
- [Repository Pattern in Python](https://www.cosmicpython.com/book/chapter_02_repository.html)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Generic Types in Python](https://docs.python.org/3/library/typing.html#typing.Generic)

---

## 🎓 XII. KEY LEARNINGS

### What We Achieved:

1. ✅ **Separation of Concerns**: Service không còn biết về Database
2. ✅ **Testability**: Có thể mock Repository dễ dàng
3. ✅ **Reusability**: BaseRepository tái sử dụng cho mọi entity
4. ✅ **Maintainability**: Đổi ORM chỉ cần sửa Repository layer
5. ✅ **SOLID Compliance**: Tuân thủ SRP, DIP, OCP

### Anti-Patterns Avoided:

- ❌ **Anemic Domain Model**: Service có business logic thực sự
- ❌ **God Object**: Không có class làm quá nhiều việc
- ❌ **Leaky Abstraction**: Service không expose Database details

---

**Document Version:** 1.0
**Created:** 2025-01-25
**Author:** Claude AI (Repository Pattern Implementation Plan)
**Status:** Ready for Implementation ✅
