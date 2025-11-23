# FastAPI Employee Search Service

A high-performance, containerized microservice built with **FastAPI** to provide an employee search directory. Designed for multi-tenancy, high scalability (millions of users), and dynamic configuration.

> **Note:** This project is a technical assignment solution focusing on API design, performance optimization, and custom implementation of core system components without external dependencies.

---

## 🚀 Key Features

* **High-Performance API:** Optimized with Deferred Join (Late Row Lookup) pagination for handling millions of records (10x-100x faster for deep pages).
* **Multi-Select Filters:** Support for selecting multiple values in location, company, department, position filters.
* **Page Jumping:** Traditional pagination with page numbers - jump to any page directly.
* **Multi-Tenancy Isolation:** Strict data separation ensures users can only search within their own organization.
* **Dynamic Column Configuration:** Return fields are dynamically masked based on per-organization settings.
* **Custom Rate Limiting:** Thread-safe, in-memory sliding window rate limiter (no Redis/external libs).
* **Containerized:** Fully Dockerized with optimized multi-stage builds.
* **OpenAPI Integration:** Auto-generated API documentation via Swagger UI.

---

## 🛠 Tech Stack

* **Language:** Python 3.10+
* **Framework:** FastAPI
* **Database:** PostgreSQL (via SQLAlchemy & AsyncPG)
* **Container:** Docker & Docker Compose
* **Testing:** Pytest

---

## 🏗 Architecture Decisions

### 1. Dynamic Columns (The "Configurable Output" Problem)
Instead of hardcoding the API response model, the system uses a configuration layer.
* **Storage:** Organization configurations (allowed columns) are stored in the database/config file.
* **Logic:** A middleware/serializer layer intercepts the response and filters out fields that are not in the organization's "allow-list". This ensures that even if the DB query selects all data, the API response remains strict and secure.

### 2. Deferred Join Pagination (High Performance)
Traditional OFFSET pagination is slow for deep pages because it reads and discards N rows.
* **Implementation:** Split query into 2 steps: (1) Get IDs using index-only scan, (2) JOIN back to fetch full data.
* **Performance:** 10x-100x faster for pages 1000+ compared to simple OFFSET.
* **Page Jumping:** Supports jumping to any page directly (unlike cursor-based pagination).

### 3. Custom Rate Limiting (No External Libs)
Per the assignment constraints, no external rate-limiting libraries (like `slowapi` or Redis) were used.
* **Implementation:** I implemented a **Sliding Window** algorithm using Python's `collections` and `time` modules.
* **Concurrency:** Used `asyncio.Lock` to ensure thread safety when modifying the in-memory request counters.
* **Cleanup:** A background mechanism periodically cleans up stale entries to prevent memory leaks.

---

## ⚡️ Quick Start

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
    *This will start the FastAPI backend and a PostgreSQL database instance.*

3.  **Seed Dummy Data:**
    The application will automatically seed initial data (3 Organizations, Configs, and **10,000 random Employees**) on startup if the DB is empty.
    *(Check logs to confirm seeding is complete).*

4.  **Access the API:**
    * **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
    * **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🔧 Shell Scripts (Mini CI/CD)

The project includes helper scripts in the `scripts/` directory:

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

## 🧪 Testing

Unit tests are written using `pytest`. To run them inside the container:

```bash
docker-compose exec app pytest