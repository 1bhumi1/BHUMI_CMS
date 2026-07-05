# College Management System Backend (FastAPI + MySQL)

A production-ready, highly secure backend for a College Management System (CMS) built with FastAPI, SQLAlchemy 2.0 (async ORM), Alembic, Pydantic V2, MySQL, and JWT Authentication.

---

## 🛠️ Technology Stack

- **Framework**: FastAPI (Asynchronous REST API)
- **Database**: MySQL 8.0 (Production) & SQLite (Testing)
- **ORM**: SQLAlchemy 2.0 (Modern Declarative Mappings)
- **Migrations**: Alembic
- **Security**: JWT Access/Refresh tokens (RS256/HS256), OAuth2 Password Flow, Bcrypt (Passlib)
- **Validation**: Pydantic v2
- **Testing**: Pytest & pytest-asyncio (aiosqlite)
- **Containerization**: Docker & Docker Compose

---

## 📂 Project Structure

```text
app/
    api/
        v1/             # Endpoint routers (auth, rbac, student, staff, academic, search, dashboard)
        router.py       # Version router aggregator
    core/               # Configuration settings (pydantic-settings)
    database/           # Async database engine & Sessionmaker
    dependencies/       # Request dependencies (auth injects, etc.)
    middleware/         # Logging latency, errors handlers, security headers, rate limiters
    models/             # SQLAlchemy ORM models (auth, academic, student, staff, system)
    permissions/        # Dynamic RBAC evaluators (has_permission dependency factory)
    repositories/       # Base CRUD repository & custom entity subclasses
    schemas/            # Pydantic v2 validation payloads and responses
    services/           # Business services (auth, student admission, staff, academic)
    audit/              # Structured audit log recorder (logs/audit.log)
    main.py             # FastAPI entrypoint bootstrap
tests/                  # pytest integration suite
```

---

## ⚙️ Prerequisites

- Python 3.12+
- MySQL 8.0 (optional if running via Docker)
- Docker & Docker Compose (for containerized setup)

---

## 🚀 Getting Started (Local Setup)

### 1. Clone the repository and navigate to root:
```bash
cd CMS_Redesign
```

### 2. Set up virtual environment and install dependencies:
```bash
python -m venv .venv
# On Windows Powershell:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Setup environment variables:
Copy the `.env.example` file to `.env` and fill in your database details and JWT secret keys:
```bash
copy .env.example .env
```

### 4. Running Migrations:
To generate migrations automatically from the models, run:
```bash
alembic revision --autogenerate -m "Initial schema migration"
alembic upgrade head
```

### 5. Running the local development server:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Interactive Swagger API documentation will be available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🐳 Docker Deployment

To launch the entire stack (FastAPI backend + MySQL 8.0 database) in Docker:

```bash
docker-compose up --build
```

- **MySQL Database**: Automatically spins up, health checks, and initializes using the schema in `campus_active.sql`.
- **Backend API**: Starts and exposes endpoints at [http://localhost:8000](http://localhost:8000).

---

## 🧪 Running Tests

We use a temporary file-based SQLite database for running integration tests to keep tests fully decoupled and fast.

Run the test suite using pytest:
```bash
python -m pytest -v
```

---

## 🛡️ Security & Architecture Best Practices

- **Strict MySQL Schema Matching**: Models are mapped directly from the single source of truth (`campus_active.sql`). Typos like `institue_id` in `department` are preserved to maintain binary compatibility.
- **Savepoint-Based Transactions**: Student admission pipeline handles multiple tables (Student, Addresses, Guardians, Qualifications) inside a single transaction. If any part fails, the entire transaction rolls back.
- **Audit Logging**: Successful logins, logouts, CRUD changes, and role assignments are written to rotating JSON files under `logs/audit.log`.
- **Dynamic RBAC Evaluation**: Permissions are verified per-request using the `Depends(has_permission("permission_name"))` dependency factory, fetching roles and permissions dynamically from the database.
