import json
import os
import re
from pathlib import Path

# Setup paths
backend_dir = Path(__file__).resolve().parent.parent
project_dir = backend_dir.parent
docs_dir = project_dir / "docs"
docs_dir.mkdir(exist_ok=True)

with open(backend_dir / "docs_metadata.json", "r") as f:
    metadata = json.load(f)

models = metadata["models"]
routes = metadata["routes"]

def format_doc_01():
    content = """# CMS Project Overview

## Technology Stack
- **Frontend**: React, TypeScript, Vite, TailwindCSS, React Hook Form, TanStack Query
- **Backend**: FastAPI, Python 3, SQLAlchemy 2.0 (Async), Pydantic v2
- **Database**: MySQL (Async drivers) / SQLite for tests
- **Authentication**: JWT (JSON Web Tokens)
- **State Management**: TanStack Query (Server state), React Context (Auth State)

## Folder Structure
```
CMS_Redesign/
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ alembic/            # Database migrations
â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ api/            # API Controllers (Routers)
â”‚   â”‚   â”œâ”€â”€ audit/          # Audit logging
â”‚   â”‚   â”œâ”€â”€ core/           # Config, Security, JWT
â”‚   â”‚   â”œâ”€â”€ database/       # DB session factory
â”‚   â”‚   â”œâ”€â”€ dependencies/   # FastAPI dependencies (Auth, etc)
â”‚   â”‚   â”œâ”€â”€ models/         # SQLAlchemy ORM Models
â”‚   â”‚   â”œâ”€â”€ permissions/    # RBAC Evaluator
â”‚   â”‚   â”œâ”€â”€ repositories/   # DB CRUD logic (No commits)
â”‚   â”‚   â”œâ”€â”€ schemas/        # Pydantic v2 DTOs
â”‚   â”‚   â””â”€â”€ services/       # Business Logic
â”‚   â”œâ”€â”€ tests/
â”‚   â””â”€â”€ scripts/
â””â”€â”€ frontend/
    â”œâ”€â”€ src/
    â”‚   â”œâ”€â”€ components/     # UI Components, Layout, PermissionGuard
    â”‚   â”œâ”€â”€ lib/            # Axios API config, AuthContext
    â”‚   â”œâ”€â”€ pages/          # Full page modules (Student, Staff, Academic)
    â”‚   â””â”€â”€ App.tsx         # Routing definitions
```

## Architecture Pattern

```mermaid
graph TD
    UI[React Frontend] --> |API Request| Route[FastAPI Router]
    Route --> |Validates Payload| Schema[Pydantic Schema]
    Route --> |Applies Business Rules| Service[Service Layer]
    Service --> |Executes Queries| Repo[Repository Layer]
    Repo --> |Maps to Objects| ORM[SQLAlchemy 2.0]
    ORM --> |Executes SQL| DB[(MySQL Database)]
    
    subgraph Transactions
        Route -.-> |async with db.begin| Service
    end
```
"""
    with open(docs_dir / "01_Project_Overview.md", "w", encoding="utf-8") as f:
        f.write(content)

def format_doc_02():
    content = "# Database Documentation\n\n"
    for model in models:
        content += f"## Table: `{model['table_name']}`\n"
        content += f"**Class**: `{model['class_name']}`\n\n"
        content += "### Columns\n"
        content += "| Column Name | Type | Primary Key | Nullable | Foreign Keys |\n"
        content += "|-------------|------|-------------|----------|--------------|\n"
        for col in model['columns']:
            fk = ", ".join(col['foreign_keys']) if col['foreign_keys'] else "-"
            content += f"| `{col['name']}` | `{col['type']}` | {col['primary_key']} | {col['nullable']} | `{fk}` |\n"
        content += "\n"
        if model['relationships']:
            content += "### Relationships\n"
            content += "| Relationship Name | Target Model | Direction |\n"
            content += "|-------------------|--------------|-----------|\n"
            for rel in model['relationships']:
                content += f"| `{rel['name']}` | `{rel['target']}` | `{rel['direction']}` |\n"
            content += "\n"
        content += "---\n\n"
    
    with open(docs_dir / "02_Database_Documentation.md", "w", encoding="utf-8") as f:
        f.write(content)

def format_doc_03():
    content = """# Entity Relationships

```mermaid
erDiagram
"""
    for model in models:
        for rel in model['relationships']:
            if rel['direction'] == 'MANYTOONE':
                content += f"    {model['class_name']} }}o--|| {rel['target']} : \"{rel['name']}\"\n"
            elif rel['direction'] == 'ONETOMANY':
                content += f"    {model['class_name']} ||--o{{ {rel['target']} : \"{rel['name']}\"\n"
            elif rel['direction'] == 'ONETOONE':
                content += f"    {model['class_name']} ||--|| {rel['target']} : \"{rel['name']}\"\n"
            elif rel['direction'] == 'MANYTOMANY':
                content += f"    {model['class_name']} }}o--o{{ {rel['target']} : \"{rel['name']}\"\n"
    content += "```\n"
    with open(docs_dir / "03_Entity_Relationships.md", "w", encoding="utf-8") as f:
        f.write(content)

def format_doc_04():
    content = """# CRUD Matrix

| Module | Create | Read | Update | Delete | Search | Filter | Export | Import | Frontend | Backend |
|--------|--------|------|--------|--------|--------|--------|--------|--------|----------|---------|
| Auth | âŒ | âœ” | âŒ | âŒ | âŒ | âŒ | âŒ | âŒ | âœ” | âœ” |
| Roles | âŒ | âœ” | âŒ | âŒ | âŒ | âŒ | âŒ | âŒ | âŒ | âœ” |
| Permissions | âŒ | âœ” | âŒ | âŒ | âŒ | âŒ | âŒ | âŒ | âŒ | âœ” |
| Staff | âœ” | âœ” | âœ” | âœ” | âœ” | âœ” | âœ” | âŒ | âœ” | âœ” |
| Student | âœ” | âœ” | âœ” | âœ” | âœ” | âœ” | âœ” | âŒ | âœ” | âœ” |
| Department | âœ” | âœ” | âœ” | âœ” | âœ” | âœ” | âœ” | âŒ | âŒ | âœ” |
| Program | âœ” | âœ” | âœ” | âœ” | âœ” | âœ” | âœ” | âŒ | âŒ | âœ” |
| Specialization | âœ” | âœ” | âœ” | âœ” | âœ” | âœ” | âœ” | âŒ | âŒ | âœ” |
| Academic Program | âœ” | âœ” | âœ” | âœ” | âœ” | âœ” | âœ” | âŒ | âœ” | âœ” |
| Academic Session | âœ” | âœ” | âœ” | âœ” | âœ” | âœ” | âœ” | âŒ | âœ” | âœ” |
| Search | âŒ | âœ” | âŒ | âŒ | âœ” | âŒ | âŒ | âŒ | âœ” | âœ” |
"""
    with open(docs_dir / "04_CRUD_Matrix.md", "w", encoding="utf-8") as f:
        f.write(content)

def format_doc_05():
    content = "# API Documentation\n\n"
    
    # Group by tags
    tags_map = {}
    for r in routes:
        tag = r['tags'][0] if r['tags'] else "Other"
        if tag not in tags_map:
            tags_map[tag] = []
        tags_map[tag].append(r)
        
    for tag, endpoints in tags_map.items():
        content += f"## {tag}\n\n"
        content += "| Method | Path | Endpoint Function | Dependencies (Auth/Permissions) |\n"
        content += "|--------|------|-------------------|--------------------------------|\n"
        for r in endpoints:
            methods = ", ".join(r['methods'])
            deps = ", ".join(r['dependencies']) if r['dependencies'] else "None"
            # Clean up deps naming
            deps = deps.replace("require_permission", "RBAC").replace("get_current_user", "Auth")
            content += f"| `{methods}` | `{r['path']}` | `{r['endpoint']}` | `{deps}` |\n"
        content += "\n"
        
    with open(docs_dir / "05_API_Documentation.md", "w", encoding="utf-8") as f:
        f.write(content)

def format_doc_06():
    content = """# RBAC Permission Matrix

| Role | Admin | Staff | Student |
|------|-------|-------|---------|
| Login | âœ” | âœ” | âœ” |
| Profile Read | âœ” | âœ” | âœ” |
| Profile Update | âœ” | âœ” | âŒ |
| Staff Read | âœ” | âœ” | âŒ |
| Staff Write | âœ” | âŒ | âŒ |
| Student Read | âœ” | âœ” | âŒ |
| Student Write | âœ” | âŒ | âŒ |
| Academic Settings | âœ” | âŒ | âŒ |
| Academic Read | âœ” | âœ” | âœ” |
| Impersonation | âœ” | âŒ | âŒ |

## Extracted Permission Strings
- `staff.read`, `staff.create`, `staff.update`, `staff.delete`
- `student.read`, `student.create`, `student.update`, `student.delete`
- `academic_program.read`, `academic_program.create`, `academic_program.update`, `academic_program.delete`
- `academic_session.read`, `academic_session.create`, `academic_session.update`, `academic_session.delete`
- `department.read`, `department.create`, `department.update`, `department.delete`
- `program.read`, `program.create`, `program.update`, `program.delete`
- `specialization.read`, `specialization.create`, `specialization.update`, `specialization.delete`
- `impersonate.execute`
"""
    with open(docs_dir / "06_RBAC_Permission_Matrix.md", "w", encoding="utf-8") as f:
        f.write(content)

def format_doc_07():
    content = """# Module Dependencies

```mermaid
graph TD
    Department --> AcademicProgram
    Program --> AcademicProgram
    Specialization --> AcademicProgram
    AcademicSession --> StudentAdmission
    AcademicProgram --> StudentAdmission
    Student --> StudentAdmission
    Student --> StudentAddress
    Student --> StudentGuardian
    Student --> StudentQualification
    Student --> StudentDocument
    Staff --> StaffDetails
    Staff --> StaffRole
    Role --> StaffRole
    Staff --> Login
    Student --> Login
```
"""
    with open(docs_dir / "07_Module_Dependencies.md", "w", encoding="utf-8") as f:
        f.write(content)

def format_doc_08():
    content = """# Business Rules

## Academic
1. **Active Session Limit**: Only ONE Academic Session may be marked as active/current. Marking a new session as active automatically unsets the previous one.
2. **Session Dates**: An Academic Session's start date must be strictly before its end date.
3. **Session Overlap**: Academic Sessions cannot have overlapping date ranges.
4. **Program Constraint**: A Specialization must belong to the selected Program when creating an Academic Program.
5. **Entry Semester Limit**: Entry semester must be <= Total Semesters.
6. **Deletion Guards**: 
   - Cannot delete an Academic Program if Student Admissions reference it.
   - Cannot delete an Academic Session if Student Admissions reference it.
   - Cannot delete a Department if Academic Programs reference it.

## Student
1. **Login Credentials**: Student password defaults to Date of Birth in DDMMYYYY format.
2. **Impersonation**: Admins can impersonate students/staff for troubleshooting.
3. **Enrollment**: A student can have multiple admissions across different sessions/programs.
4. **Status**: Students are active by default upon creation.

## Staff
1. **Designations**: Super Admin legacy designation has been migrated to Admin.
2. **Roles**: A staff member can have multiple RBAC roles attached (e.g. HOD, Admin, Faculty).
"""
    with open(docs_dir / "08_Business_Rules.md", "w", encoding="utf-8") as f:
        f.write(content)

def format_doc_09():
    content = """# Project Progress

## Implemented
- Authentication (JWT, Roles)
- RBAC Evaluator & Middleware
- Impersonation System
- Staff CRUD
- Student CRUD
- Academic Hierarchy (Departments, Programs, Specializations) - Backend
- Academic Program Management - Full Stack
- Academic Session Management - Full Stack

## Partially Implemented
- Departments, Programs, Specializations Management (Frontend UI missing)
- Dashboard Analytics (Mock data/basic widgets)
- Export Data (Basic CSV export exists for some modules)

## Not Implemented
- Attendance Module
- Examination / Results Module
- Fees Management
- Timetable Scheduling
- Library Management
- Transport / Hostel Management
- HR / Payroll
- Communication / Announcements
"""
    with open(docs_dir / "09_Project_Progress.md", "w", encoding="utf-8") as f:
        f.write(content)

def format_doc_10():
    content = """# Development Roadmap

## Recommended Implementation Order

1. **Frontend for Academic Hierarchy** (Departments, Programs, Specializations)
   *Why*: Completes the foundational academic structure. These modules have complete backend APIs but need UI parity.
2. **Academic Term / Semesters**
   *Why*: Essential stepping stone for timetable and subjects.
3. **Subjects / Course Management**
   *Why*: Defines what students will study in an academic program term.
4. **Faculty Subject Mapping**
   *Why*: Connects Staff (Faculty) to Subjects before a timetable can be generated.
5. **Timetable / Class Schedules**
   *Why*: Requires Subjects, Faculty, and Terms.
6. **Attendance Module**
   *Why*: Faculty cannot mark attendance without a timetable and enrolled students.
7. **Examination & Results**
   *Why*: Relies on Subjects and Students to record marks.
8. **Fees & Payments**
   *Why*: Can be developed in parallel, but depends heavily on Admissions and Sessions to generate fee structures.
9. **Auxiliary Modules** (Library, Hostel, Transport)
   *Why*: Peripheral modules that rely on the existence of both Staff and Students but don't block core academic workflows.
"""
    with open(docs_dir / "10_Roadmap.md", "w", encoding="utf-8") as f:
        f.write(content)

def format_doc_11():
    content = """# Code Quality Report

## Transaction Handling
- **Pattern**: Standardized to `async with db.begin():` explicitly inside the FastAPI Router (Controller).
- **Service Layer**: No transactions inside the service layer; it strictly executes business rules.
- **Dependency Leaks**: Implicit transactions caused by Auth/RBAC dependencies (`get_current_user`) have been actively tracked and explicitly closed using `await db.commit()` at the end of GET routes to prevent `InvalidRequestError` and asyncio event loop freezes.

## SQLAlchemy Optimization
- **Eager Loading**: The repositories aggressively use `contains_eager` combined with `join` for list operations to prevent N+1 query problems.
- **Single fetching**: `selectinload` is appropriately used for fetching single records by ID with heavy relationship trees.

## Pydantic Architecture
- **v2 Standardization**: All schemas employ `model_config = ConfigDict(from_attributes=True)`. This resolves earlier `ValidationError` issues when mapping SQLAlchemy lazy-loaded or relationship objects directly into FastAPI responses.

## Debt / Smells
- **Hardcoded Options**: Enums in SQLAlchemy models (e.g., student admission type, address type) are hardcoded in the database schema. Migration to reference tables might be required for extreme scalability.
"""
    with open(docs_dir / "11_Code_Quality_Report.md", "w", encoding="utf-8") as f:
        f.write(content)

def format_doc_12():
    content = """# Security Audit

## Authentication
- **Mechanism**: JWT (Access Token + Refresh Token). 
- **Storage**: Currently, local storage is presumed for JWTs on frontend. Need to verify XSS risks. HttpOnly Cookies are recommended for production.
- **Passwords**: Hashed using `passlib` (bcrypt). Safe.

## Authorization (RBAC)
- **Granular Permissions**: Evaluator enforces strict role checks (e.g., `academic_program.create`) before route execution.
- **Impersonation**: Admins can log in as users. Guarded by the `impersonate.execute` permission. Logs are generated in `ImpersonationLog` to maintain an audit trail.

## API Security
- **CORS**: Configured in `main.py`.
- **SQL Injection**: SQLAlchemy 2.0 ORM strictly uses parameterized queries. Raw SQL injection is not possible through current repositories.
- **Validation**: Pydantic v2 ensures strict type boundaries and max string lengths, mitigating buffer overflows and excessive payload attacks.

## Data Exposure
- **Passwords**: Pydantic response models explicitly exclude password hashes.
- **Soft Deletes**: System primarily uses hard deletes guarded by reference checks. Implementing soft deletes for auditability (e.g., `is_deleted` flags) is recommended for financial modules (Fees).
"""
    with open(docs_dir / "12_Security_Audit.md", "w", encoding="utf-8") as f:
        f.write(content)

def format_doc_13():
    content = """# Architecture Diagrams

## Complete Flow
```mermaid
graph LR
    Client((Client App)) --> |HTTP Requests| Nginx[Reverse Proxy]
    Nginx --> FastAPI[FastAPI App]
    FastAPI --> Auth[RBAC & JWT Middleware]
    Auth --> Router[API Router]
    Router --> Services[Business Services]
    Services --> Repos[Repositories]
    Repos --> DB[(MySQL / SQLite)]
```

## Transaction Lifecycle
```mermaid
sequenceDiagram
    participant C as Client
    participant A as API Route
    participant S as Service
    participant R as Repository
    participant D as Database

    C->>A: POST /endpoint
    A->>D: async with db.begin()
    A->>S: validate_and_execute()
    S->>R: check_rules()
    R->>D: SELECT ...
    S->>R: execute_mutation()
    R->>D: INSERT/UPDATE ...
    A->>D: Commit (End context block)
    A->>C: Return 201 Response
```
"""
    with open(docs_dir / "13_Architecture_Diagrams.md", "w", encoding="utf-8") as f:
        f.write(content)

def format_doc_14():
    total_tables = len(models)
    total_routes = len(routes)
    
    content = f"""# Executive Project Summary

## Metrics
- **Total Database Tables**: {total_tables}
- **Total API Routes**: {total_routes}
- **Total Full Stack CRUD Modules**: 4 (Staff, Student, Academic Program, Academic Session)
- **Partially Implemented Modules**: 3 (Department, Program, Specialization - Backend only)
- **Missing Modules**: Attendance, Exams, Fees, Timetable, Library, Transport, Hostel

## Conclusion
The College Management System (CMS) possesses a highly robust, scalable architecture using modern technologies (FastAPI, SQLAlchemy 2.0, React, TanStack Query). The architectural blueprint (API owning transactions, Service for business logic, Repositories for queries) is well established and consistently executed.

The priority moving forward should be resolving the "Partially Implemented" modules by building their frontend interfaces, before proceeding linearly down the academic hierarchy (Terms -> Subjects -> Timetables -> Attendance -> Results).
"""
    with open(docs_dir / "14_Project_Summary.md", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    format_doc_01()
    format_doc_02()
    format_doc_03()
    format_doc_04()
    format_doc_05()
    format_doc_06()
    format_doc_07()
    format_doc_08()
    format_doc_09()
    format_doc_10()
    format_doc_11()
    format_doc_12()
    format_doc_13()
    format_doc_14()
    print("Generated all 14 documentation files in docs/")
