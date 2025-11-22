# Project Requirements: HR Employee Search Microservice

## 1. Project Overview

The goal is to build a high-performance microservice for an HR company using **FastAPI**. [cite_start]The primary
function is to provide an **Employee Search API** that populates a search directory[cite: 3, 4].

[cite_start]The system must be designed to handle heavy loads (millions of users), support multi-tenancy with strict
data isolation, and allow dynamic column configuration per organization.

---

## 2. Functional Requirements

### 2.1. Search API

* [cite_start]**Endpoint:** Implement a robust search API (GET request)[cite: 6].
* [cite_start]**Filtering:** The API must support filtering by the following fields[cite: 10]:
    * `Status` (Active, Not started, Terminated).
    * `Location`.
    * `Company`.
    * `Department`.
    * `Position`.
* [cite_start]**Pagination:** Although not explicitly stated, pagination is implied due to the requirement of handling "
  millions of users" to ensure performance.

### 2.2. Dynamic Response (Dynamic Columns)

* [cite_start]Different organizations require different columns in the search output[cite: 12].
* [cite_start]The system must allow configuration of visible columns at the organization level[cite: 14].
* [cite_start]**Constraint:** No CRUD API needed for this configuration; it can be stored in a DB seed file or config
  file[cite: 15, 16].

### 2.3. Data Privacy & Security (Multi-tenancy)

* [cite_start]**Strict Isolation:** Users from Organization A must NOT see users from Organization B[cite: 31].
* [cite_start]**Attribute Hiding:** Ensure extra attributes not configured for the organization are not leaked in the
  API response[cite: 31].

---

## 3. Non-Functional Requirements

### 3.1. Performance

* [cite_start]**Scale:** Design the API to handle **millions of users**.
* **Optimization:** Database indexing and efficient query design are required.

### 3.2. Rate Limiting

* [cite_start]**System:** Implement a rate-limiting mechanism to prevent abuse[cite: 20].
* **Constraint:** **NO external libraries** allowed for rate-limiting. [cite_start]Must be a custom implementation using
  Python's standard library.

### 3.3. Technology Stack & Environment

* [cite_start]**Language/Framework:** Python / FastAPI[cite: 32].
* [cite_start]**Environment:** Must execute correctly in a Linux/Unix environment[cite: 25, 38].
* [cite_start]**Containerization:** The service must be containerized (Docker)[cite: 27].

### 3.4. Quality Assurance

* [cite_start]**Testing:** The API must be **Unit Tested**[cite: 29]. [cite_start]External testing libraries (e.g.,
  `pytest`) are allowed[cite: 37].
* [cite_start]**Documentation:** API information must be sharable in **OpenAPI** format (Swagger)[cite: 28].

---

## 4. Technical Constraints (Strict)

1. [cite_start]**No External Dependencies for Logic:** Only standard libraries are allowed for core logic (especially
   rate-limiting)[cite: 36].
2. **Scope limit:**
    * [cite_start]Ignore "Add Employee", "Import", "Export" features[cite: 7].
    * [cite_start]No CRUD APIs for entities (Users, Org, etc.)[cite: 9].
    * [cite_start]No need for complex migration relationships; focus on the API[cite: 33].

---

## 5. Deliverables

1. [cite_start]**Source Code:** GitHub repository link[cite: 23].
2. [cite_start]**Documentation:** A `README.md` containing installation and usage instructions for a
   developer[cite: 24].
3. **Tests:** Comprehensive unit tests.
4. **Docker:** Dockerfile/Docker-compose for easy setup.