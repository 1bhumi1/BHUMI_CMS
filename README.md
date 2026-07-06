# 🎓 College Management System (CMS) Redesign

A production-ready, enterprise-grade **College Management System (CMS)** featuring a secure, asynchronous **FastAPI** backend and a dynamic, responsive **React + TypeScript** frontend. 

The system implements advanced design patterns including custom dynamic Role-Based Access Control (RBAC), multi-table database transactions with savepoint rollbacks, rotating JWT token validation (Access & Refresh tokens), and a structured audit logging system.

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Asynchronous REST API)
- **Database**: MySQL 8.0 (Production) & SQLite (Testing)
- **ORM**: SQLAlchemy 2.0 (Modern Declarative Async Mappings)
- **Migrations**: Alembic
- **Security**: JWT Access & Refresh token rotation, OAuth2 Password Flow, Bcrypt (Passlib)
- **Validation**: Pydantic v2
- **Testing**: Pytest & pytest-asyncio (aiosqlite)
- **Deployment**: Docker & Docker Compose

### Frontend
- **Framework & Build Tool**: React 18, TypeScript, Vite
- **Styling**: Tailwind CSS 3, PostCSS, Lucide React (Icons)
- **Routing**: React Router DOM (v6)
- **State Management & Async Operations**: TanStack React Query (v5)
- **Form Handling & Validation**: React Hook Form, Zod
- **HTTP Client**: Axios (with custom automatic token refresh interceptors)

---

## 📂 Project Architecture

The project is structured as a monorepo containing a dedicated backend service and a frontend single-page application:

```text
CMS_Redesign/
├── backend/                  # FastAPI Backend Application
│   ├── app/
│   │   ├── api/              # Endpoint routers (v1 API routers)
│   │   ├── audit/            # Structured audit log recorder
│   │   ├── core/             # Configuration settings (pydantic-settings)
│   │   ├── database/         # Async database engine & Sessionmaker
│   │   ├── dependencies/     # Request dependencies (auth injects, etc.)
│   │   ├── middleware/       # Custom middleware (CORS, Rate Limiter, Latency Logger)
│   │   ├── models/           # SQLAlchemy ORM models (Academic, Student, Staff, System)
│   │   ├── permissions/      # Dynamic RBAC evaluators (has_permission factory)
│   │   ├── repositories/     # Base Async CRUD repository & custom entity subclasses
│   │   ├── schemas/          # Pydantic v2 validation payloads & responses
│   │   └── services/         # Business services (Auth, Admission, LMS, Feedback)
│   ├── scripts/              # Database schema migrations, seeding, utility scripts
│   └── tests/                # pytest integration suite
├── frontend/                 # React Frontend Application
│   ├── dist/                 # Production compiled builds
│   ├── src/
│   │   ├── components/       # Reusable layout and UI elements (Sidebar, ProtectedRoute)
│   │   ├── lib/              # AuthContext, API client Axios configurations
│   │   └── pages/            # Page modules (Academics, LMS, Feedback360, Dashboards)
└── docker-compose.yml        # Docker Multi-container Orchestration
```

For more specific architecture details, view the sub-project guides:
- [backend/README.md](file:///d:/cms%20redesign/CMS_Redesign/backend/README.md)
- [frontend/README.md](file:///d:/cms%20redesign/CMS_Redesign/frontend/README.md)

---

## 🌟 Key Features

### 🔑 Advanced Authentication & Dynamic RBAC
- OAuth2 password grant flow with separate JWT Access and Refresh tokens.
- Automatic token refresh interceptors on the frontend to ensure a seamless user experience.
- Dynamic permission checking utilizing a custom FastAPI dependency factory `Depends(has_permission("permission_name"))` that validates users against database-driven roles and permissions.

### 🏛️ Academic Structure Management
- Modular management of high-level college structures including **Institutes**, **Departments**, **Programs**, **Specializations**, **Academic Sessions**, and **Terms/Semesters**.

### 💼 Leave Management System (LMS)
- Complete faculty/staff leave lifecycle tracker.
- Custom configurations for leave types and maximum leave limits.
- Real-time leave balance calculations, request submissions, and multi-tier approval workflows.

### 📝 Feedback360 System
- A comprehensive 360-degree feedback module allowing administrators to design and deploy surveys.
- Anonymous responses, target participant configurations, and interactive visual reporting graphs for feedback analysis.

### 🛡️ Enterprise Security & Integrity
- **Strict DB Schema Adherence**: SQL models map precisely to physical schemas to prevent binary incompatibility.
- **Transactional Consistency**: Multi-table student admission flows use database Savepoint-based transaction rollback blocks.
- **Rate-Limiting**: Custom middleware to mitigate brute force attacks and denial-of-service attempts.
- **Structured Audit Logs**: All administrative actions (user login/logout, CRUD operations, role mutations) write to structured rotating JSON audit logs.

---

## 🚀 Getting Started

### Prerequisites
Make sure you have the following installed:
- Python 3.12+
- Node.js v18+ (with npm)
- MySQL 8.0 (optional, if running locally without Docker)
- Docker & Docker Compose

---

### 🐳 Method A: Run via Docker Compose (Recommended)

To spin up the entire application stack (MySQL Database + FastAPI Backend + Pre-built frontend client) instantly, run from the root directory:

```bash
docker-compose up --build
```

- **Database**: Port `3306` (Initialized with Schema in `backend/campus_active.sql`)
- **Backend API**: Port `8000` (Interactive docs available at [http://localhost:8000/docs](http://localhost:8000/docs))

---

### ⚙️ Method B: Local Development Setup

If you wish to run backend and frontend separately in development mode:

#### 1. Setup Backend API
From the root directory:
```bash
# 1. Navigate to backend folder
cd backend

# 2. Set up virtual environment and activate
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# 3. Install packages
pip install -r requirements.txt

# 4. Set up environment variables
copy .env.example .env

# 5. Execute DB Migrations and Seed Master Data
alembic upgrade head
python scripts/seed.py

# 6. Start the API development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

#### 2. Setup Frontend Client
From the root directory:
```bash
# 1. Navigate to frontend folder
cd frontend

# 2. Install dependencies
npm install

# 3. Setup environment variables
# Create a .env file containing:
# VITE_API_URL=http://localhost:8000/api/v1

# 4. Start the Vite server
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🔐 Default Accounts & Login Credentials

After running the database seed script `python scripts/seed.py`, the following demo accounts are created for testing different user roles:

| Role | Username (Computer Code) | Password |
|---|---|---|
| **Admin** | `ADMIN001` | `Admin@123` |
| **Principal** | `EMP1001` | `Admin@123` |
| **HOD** | `EMP1002` | `Admin@123` |
| **Faculty** | `EMP1003` | `Admin@123` |
| **Accountant** | `ACC001` | `Admin@123` |
| **Librarian** | `LIB001` | `Admin@123` |
| **Student** | `2025001` | `Student@123` |
| **Parent** | `2025002` | `Parent@123` |

---

## 🧪 Testing Backend

The backend contains a suite of integration tests configured with Pytest, using a detached SQLite instance.

Run tests from the `backend/` directory:
```bash
pytest -v
```
