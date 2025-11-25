# IMPACTED FILES - DETAILED BREAKDOWN

> Chi tiết về các files bị ảnh hưởng khi triển khai Repository Pattern

---

## 📁 CẤU TRÚC THỦ MỤC - BEFORE vs AFTER

### BEFORE (Current Structure)
```
app/
├── __init__.py
├── main.py                          # ✅ NO CHANGE
├── config.py                        # ✅ NO CHANGE
├── database.py                      # ✅ NO CHANGE
├── seed_data.py                     # ✅ NO CHANGE
│
├── api/
│   ├── __init__.py
│   └── employees.py                 # ⚠️ MINOR CHANGE (imports only)
│
├── core/
│   ├── __init__.py
│   └── dependencies.py              # 🔧 MAJOR REFACTOR
│
├── services/
│   ├── __init__.py
│   └── employee_service.py          # 🔧 MAJOR REFACTOR
│
├── models/
│   ├── __init__.py                  # ✅ NO CHANGE
│   ├── base.py                      # ✅ NO CHANGE
│   ├── employee.py                  # ✅ NO CHANGE
│   └── organization.py              # ✅ NO CHANGE
│
├── schemas/
│   ├── __init__.py                  # ✅ NO CHANGE
│   └── employee.py                  # ✅ NO CHANGE
│
└── middleware/
    ├── __init__.py                  # ✅ NO CHANGE
    └── rate_limiter.py              # ✅ NO CHANGE
```

### AFTER (With Repository Layer)
```
app/
├── __init__.py
├── main.py                          # ✅ NO CHANGE
├── config.py                        # ✅ NO CHANGE
├── database.py                      # ✅ NO CHANGE
├── seed_data.py                     # ✅ NO CHANGE
│
├── api/
│   ├── __init__.py
│   └── employees.py                 # ⚠️ MINOR CHANGE
│
├── core/
│   ├── __init__.py
│   └── dependencies.py              # 🔧 REFACTORED (25 → 60 LOC)
│
├── services/
│   ├── __init__.py
│   └── employee_service.py          # 🔧 REFACTORED (202 → 120 LOC)
│
├── repositories/                    # 🆕 NEW FOLDER
│   ├── __init__.py                  # 🆕 NEW (10 LOC)
│   ├── base.py                      # 🆕 NEW (150 LOC)
│   ├── employee_repository.py       # 🆕 NEW (200 LOC)
│   └── organization_repository.py   # 🆕 NEW (80 LOC)
│
├── models/
│   ├── __init__.py                  # ✅ NO CHANGE
│   ├── base.py                      # ✅ NO CHANGE
│   ├── employee.py                  # ✅ NO CHANGE
│   └── organization.py              # ✅ NO CHANGE
│
├── schemas/
│   ├── __init__.py                  # ✅ NO CHANGE
│   └── employee.py                  # ✅ NO CHANGE
│
└── middleware/
    ├── __init__.py                  # ✅ NO CHANGE
    └── rate_limiter.py              # ✅ NO CHANGE
```

---

## 🔧 FILES REQUIRING MAJOR REFACTOR

### 1. `app/services/employee_service.py`

**Impact Level:** 🔴 CRITICAL - 40% code change

#### Changes Required:

| Section | Lines | Action | New Lines |
|---------|-------|--------|-----------|
| Imports | 1-6 | 🔄 UPDATE | Add Repository imports |
| `__init__()` | 12-13 | 🔄 REPLACE | Change from `db` to `employee_repo, org_repo` |
| `get_organization_config()` | 15-22 | 🔄 REPLACE | 1-line call to `org_repo.get_visible_columns()` |
| `validate_organization()` | 24-31 | 🔄 REPLACE | 1-line call to `org_repo.exists_and_active()` |
| `get_filter_options()` | 33-83 | 🔄 REPLACE | Loop calling `employee_repo.get_distinct_values()` |
| `search_employees()` | 85-178 | 🔄 REPLACE | 1-line call to `employee_repo.find_by_organization()` |
| `filter_employee_columns()` | 180-202 | ✅ KEEP | No change (business logic) |

#### Detailed Line-by-Line Changes:

**A. Imports (Lines 1-6)**
```python
# ❌ REMOVE
from sqlalchemy import select, func, or_, distinct

# ✅ ADD
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.organization_repository import OrganizationRepository
```

**B. Constructor (Lines 12-13)**
```python
# ❌ OLD
def __init__(self, db: AsyncSession):
    self.db = db

# ✅ NEW
def __init__(
    self,
    employee_repo: EmployeeRepository,
    org_repo: OrganizationRepository
):
    self.employee_repo = employee_repo
    self.org_repo = org_repo
```

**C. Method: `get_organization_config()` (Lines 15-22)**
```python
# ❌ OLD (8 lines)
async def get_organization_config(self, organization_id: int) -> Optional[list[str]]:
    result = await self.db.execute(
        select(OrganizationConfig.visible_columns)
        .where(OrganizationConfig.organization_id == organization_id)
    )
    config = result.scalar_one_or_none()
    return config if config else None

# ✅ NEW (2 lines)
async def get_organization_config(self, organization_id: int) -> Optional[list[str]]:
    return await self.org_repo.get_visible_columns(organization_id)
```

**D. Method: `validate_organization()` (Lines 24-31)**
```python
# ❌ OLD (8 lines)
async def validate_organization(self, organization_id: int) -> bool:
    result = await self.db.execute(
        select(Organization.id)
        .where(Organization.id == organization_id)
        .where(Organization.is_active == True)
    )
    return result.scalar_one_or_none() is not None

# ✅ NEW (2 lines)
async def validate_organization(self, organization_id: int) -> bool:
    return await self.org_repo.exists_and_active(organization_id)
```

**E. Method: `get_filter_options()` (Lines 33-83 → ~20 lines)**
```python
# ❌ OLD (50 lines - duplicated queries for 4 fields)
async def get_filter_options(self, organization_id: int) -> dict[str, list[str]]:
    # Get distinct locations (12 lines)
    locations_result = await self.db.execute(...)
    locations = [row[0] for row in locations_result.fetchall()]

    # Get distinct companies (12 lines)
    companies_result = await self.db.execute(...)
    companies = [row[0] for row in companies_result.fetchall()]

    # Get distinct departments (12 lines)
    departments_result = await self.db.execute(...)
    departments = [row[0] for row in departments_result.fetchall()]

    # Get distinct positions (12 lines)
    positions_result = await self.db.execute(...)
    positions = [row[0] for row in positions_result.fetchall()]

    return {...}

# ✅ NEW (10 lines - DRY with loop)
async def get_filter_options(self, organization_id: int) -> dict[str, list[str]]:
    filter_fields = ["location", "company", "department", "position"]

    options = {}
    for field in filter_fields:
        options[f"{field}s"] = await self.employee_repo.get_distinct_values(
            organization_id, field
        )

    return options
```

**F. Method: `search_employees()` (Lines 85-178 → ~25 lines)**
```python
# ❌ OLD (94 lines)
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
    # Build base conditions (10 lines)
    conditions = [...]

    # Handle include_terminated (3 lines)
    if not include_terminated:...

    # Text search (8 lines)
    if q:...

    # Apply status filter (8 lines)
    if status:...

    # Apply multi-select filters (12 lines)
    if locations:...
    if companies:...
    if departments:...
    if positions:...

    # Step 1: Count total (3 lines)
    count_query = select(func.count(...))
    total_result = await self.db.execute(...)
    total = total_result.scalar()

    # Step 2: Deferred Join - Get IDs only (8 lines)
    offset = (page - 1) * page_size
    id_subquery = (select(Employee.id)...).subquery()

    # Step 3: JOIN back (7 lines)
    query = (select(Employee).join(...))

    # Execute query (4 lines)
    result = await self.db.execute(query)
    employees = list(result.scalars().all())

    return employees, total

# ✅ NEW (15 lines)
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

**Summary of Changes:**
- **Lines removed:** 82 (mostly SQL queries)
- **Lines added:** 30 (repository method calls)
- **Net change:** -52 LOC (202 → 150 → 120 after cleanup)

---

### 2. `app/core/dependencies.py`

**Impact Level:** 🟡 MEDIUM - 35 new LOC

#### Changes Required:

```python
# ❌ CURRENT (25 LOC)
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.employee_service import EmployeeService

async def get_organization_id(
    x_organization_id: int = Header(...)
) -> int:
    if x_organization_id <= 0:
        raise HTTPException(...)
    return x_organization_id

async def get_employee_service(
    db: AsyncSession = Depends(get_db)
) -> EmployeeService:
    return EmployeeService(db)

# ✅ NEW (60 LOC)
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.employee_service import EmployeeService
from app.repositories.employee_repository import EmployeeRepository  # NEW
from app.repositories.organization_repository import OrganizationRepository  # NEW

async def get_organization_id(
    x_organization_id: int = Header(...)
) -> int:
    """Extract and validate organization ID from header."""
    if x_organization_id <= 0:
        raise HTTPException(...)
    return x_organization_id

# ===== NEW: Repository Factories =====

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

# ===== REFACTORED: Service Factory =====

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

**Changes:**
- **Lines added:** 35 (2 new factories + refactor existing)
- **Lines removed:** 0
- **Net change:** +35 LOC (25 → 60)

---

### 3. `app/api/employees.py`

**Impact Level:** 🟢 MINOR - Import changes only

#### Changes Required:

**Current imports:**
```python
from app.core.dependencies import get_organization_id, get_employee_service
from app.services.employee_service import EmployeeService
```

**No changes needed!** The API layer doesn't care how the Service gets its dependencies.

**Why no changes?**
- API vẫn inject `EmployeeService` qua `Depends(get_employee_service)`
- Dependency Injection framework tự động resolve repositories
- Abstraction layer hoạt động đúng ✅

---

## 🆕 NEW FILES TO CREATE

### 1. `app/repositories/__init__.py`

**LOC:** 10
**Purpose:** Export các repositories để dễ import

```python
"""
Repository layer for data access abstraction.
Contains Generic BaseRepository and specific repositories for each entity.
"""
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

### 2. `app/repositories/base.py`

**LOC:** 150
**Purpose:** Generic CRUD operations cho mọi entity
**Complexity:** ⭐⭐⭐ High (Generic Types, AsyncSession)

**Key Methods:**
- `get_by_id(id: int) → Optional[T]`
- `get_all(skip: int, limit: int) → List[T]`
- `create(**kwargs) → T`
- `update(id: int, **kwargs) → Optional[T]`
- `delete(id: int) → bool`
- `soft_delete(id: int) → bool`
- `count() → int`
- `exists(id: int) → bool`

**Dependencies:**
- `typing.Generic`, `TypeVar`
- `sqlalchemy.ext.asyncio.AsyncSession`
- `sqlalchemy.select`, `func`, `update`, `delete`

---

### 3. `app/repositories/employee_repository.py`

**LOC:** 200
**Purpose:** Employee-specific queries
**Complexity:** ⭐⭐⭐⭐ Very High (Most complex repository)

**Key Methods:**
- `find_by_organization(org_id, filters, page, page_size) → Tuple[List[Employee], int]`
  - ⚠️ Most complex: Deferred Join pagination + Dynamic filters
  - Migrated from `EmployeeService.search_employees()`
- `get_distinct_values(org_id, column_name) → List[str]`
  - Used for filter dropdowns
  - Migrated from `EmployeeService.get_filter_options()`
- `exists_by_organization(org_id) → bool`
- `_build_search_conditions(org_id, filters) → list` (private helper)
- `_count_with_conditions(conditions) → int` (private helper)

**Dependencies:**
- `app.repositories.base.BaseRepository`
- `app.models.employee.Employee`, `EmployeeStatus`
- `sqlalchemy.select`, `func`, `or_`, `distinct`

---

### 4. `app/repositories/organization_repository.py`

**LOC:** 80
**Purpose:** Organization-specific queries
**Complexity:** ⭐⭐ Medium

**Key Methods:**
- `get_active_by_id(org_id) → Optional[Organization]`
- `exists_and_active(org_id) → bool`
  - Migrated from `EmployeeService.validate_organization()`
- `get_visible_columns(org_id) → Optional[List[str]]`
  - Migrated from `EmployeeService.get_organization_config()`

**Dependencies:**
- `app.repositories.base.BaseRepository`
- `app.models.organization.Organization`, `OrganizationConfig`
- `sqlalchemy.select`

---

## 📊 IMPACT SUMMARY TABLE

| Category | Files | LOC Before | LOC After | Change |
|----------|-------|------------|-----------|--------|
| **New Files** | 4 | 0 | 440 | +440 |
| **Major Refactor** | 2 | 227 | 180 | -47 |
| **Minor Changes** | 1 | 165 | 165 | 0 |
| **No Changes** | 10 | 800 | 800 | 0 |
| **TOTAL** | 17 | ~1,192 | ~1,585 | +393 |

### Breakdown by Impact Level:

| Impact Level | Files | Examples |
|--------------|-------|----------|
| 🔴 **CRITICAL** (40%+ change) | 1 | `employee_service.py` |
| 🟡 **MEDIUM** (10-40% change) | 1 | `dependencies.py` |
| 🟢 **MINOR** (<10% change) | 1 | `employees.py` (imports only) |
| ✅ **NO CHANGE** | 10 | All models, schemas, configs |
| 🆕 **NEW FILES** | 4 | All repositories |

---

## 🧪 TESTING IMPACT

### New Test Files Required:

```
tests/repositories/
├── __init__.py
├── test_base_repository.py          # 🆕 NEW (50 LOC)
├── test_employee_repository.py      # 🆕 NEW (150 LOC)
└── test_organization_repository.py  # 🆕 NEW (80 LOC)

tests/services/
└── test_employee_service.py         # 🔄 REFACTOR (update mocks)

tests/api/
└── test_employees_api.py            # ✅ NO CHANGE (E2E tests should still pass)
```

**Testing Strategy:**
1. **Unit Tests** cho mỗi Repository (mock database)
2. **Integration Tests** cho Service (mock repositories)
3. **E2E Tests** cho API (real database)

---

## 🔍 DEPENDENCY GRAPH - BEFORE vs AFTER

### BEFORE:
```
employees.py (API)
    ↓ Depends(get_employee_service)
employee_service.py (Service)
    ↓ self.db: AsyncSession
database.py
    ↓
PostgreSQL
```

### AFTER:
```
employees.py (API)
    ↓ Depends(get_employee_service)
employee_service.py (Service)
    ↓ self.employee_repo / self.org_repo
employee_repository.py (Repository)
    ↓ self.db: AsyncSession
organization_repository.py (Repository)
    ↓ self.db: AsyncSession
database.py
    ↓
PostgreSQL
```

---

## ⚠️ CRITICAL DEPENDENCIES

### Files that MUST be created in order:

1. **First:** `app/repositories/base.py`
   - Reason: `EmployeeRepository` và `OrganizationRepository` kế thừa từ `BaseRepository`

2. **Second:** `app/repositories/employee_repository.py` + `organization_repository.py`
   - Reason: Service cần cả 2 repositories này

3. **Third:** `app/core/dependencies.py` (refactor)
   - Reason: Cần import repositories

4. **Fourth:** `app/services/employee_service.py` (refactor)
   - Reason: Phụ thuộc vào repositories và dependencies

5. **Last:** Tests và Documentation

---

## 🎯 VERIFICATION COMMANDS

### Check SQL queries removed from Service:
```bash
grep -n "self.db.execute" app/services/employee_service.py
# Expected: No results ✅

grep -n "select(" app/services/employee_service.py
# Expected: No results ✅

grep -n "from sqlalchemy import" app/services/employee_service.py
# Expected: No results ✅
```

### Check imports updated:
```bash
grep -n "EmployeeRepository" app/services/employee_service.py
# Expected: Found in imports ✅

grep -n "OrganizationRepository" app/services/employee_service.py
# Expected: Found in imports ✅
```

### Count repository methods:
```bash
grep -c "^    async def" app/repositories/employee_repository.py
# Expected: 8-10 methods ✅

grep -c "^    async def" app/repositories/organization_repository.py
# Expected: 3-5 methods ✅
```

---

**Document Version:** 1.0
**Related Documents:**
- [REPOSITORY_PATTERN_ANALYSIS.md](./REPOSITORY_PATTERN_ANALYSIS.md) - Full implementation plan
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - Quick reference
