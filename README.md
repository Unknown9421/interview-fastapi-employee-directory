# FastAPI Employee Search Service

A high-performance, containerized microservice built with **FastAPI** to provide an employee search directory. Designed for multi-tenancy, high scalability (millions of users), and dynamic configuration.

> **Note:** This project is a technical assignment solution focusing on API design, performance optimization, and custom implementation of core system components without external dependencies.

---

## 🚀 Key Features

* **High-Performance Search API:** Optimized for handling millions of records using database indexing and efficient query planning.
* **Multi-Tenancy Isolation:** Strict data separation ensures users can only search within their own organization.
* **Dynamic Column Configuration:** Return fields are dynamically masked based on per-organization settings (e.g., some orgs see "Phone", others don't).
* **Custom Rate Limiting:** A thread-safe, in-memory rate limiter implementation (Token Bucket/Fixed Window) built purely with the Python standard library (No Redis/Memcached used, per requirements).
* **Containerized:** Fully Dockerized for easy deployment.
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

### 2. Custom Rate Limiting (No External Libs)
Per the assignment constraints, no external rate-limiting libraries (like `slowapi` or Redis) were used.
* **Implementation:** I implemented a **Sliding Window** (or Token Bucket) algorithm using Python's `collections` and `time` modules.
* **Concurrency:** Used `threading.Lock` (or `asyncio.Lock`) to ensure thread safety when modifying the in-memory request counters.
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
    The application will automatically seed initial data (Organizations, Configs, and random Users) on startup if the DB is empty.
    *(Check logs to confirm seeding is complete).*

4.  **Access the API:**
    * **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
    * **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Testing

Unit tests are written using `pytest`. To run them inside the container:

```bash
docker-compose exec app pytest