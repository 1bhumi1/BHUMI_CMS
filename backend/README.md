# CMS Backend API

## Project Setup

To get started, install dependencies and set up the environment:
```bash
pip install -r requirements.txt
```

Ensure your `.env` file is properly configured with your MySQL database URL:
```
DATABASE_URL="mysql+aiomysql://root:password@127.0.0.1:3306/campus_active"
SYNC_DATABASE_URL="mysql+pymysql://root:password@127.0.0.1:3306/campus_active"
```

## Running Database Migrations

This project uses SQLAlchemy and Alembic for migrations.
To run the migrations and create the tables, execute:
```bash
alembic upgrade head
```

## Database Seeding

To insert the master data, roles, permissions, staff, students, and default login accounts into the database, run the seed script:
```bash
python scripts/seed.py
```
*(Make sure you run this from within the `backend` directory).*

### Default Login Credentials

The seed script creates the following default accounts. Note that the usernames are stored in the `computer_code` column, which is an integer:

| Role | Username / Computer Code | Password |
|---|---|---|
| Admin | ADMIN001 | Admin@123 |
| Principal | EMP1001 | Admin@123 |
| HOD | EMP1002 | Admin@123 |
| Faculty | EMP1003 | Admin@123 |
| Accountant | ACC001 | Admin@123 |
| Librarian | LIB001 | Admin@123 |
| Student | 2025001 | Student@123 |
| Parent | 2025002 | Parent@123 |

### Example API Login Request

To login and receive a JWT token, make a `POST` request to `/api/v1/auth/login` (or `/login`). For example:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
           "username": "ADMIN001",
           "password": "Admin@123"
         }'
```

### Expected JWT Response

Upon successful authentication, the API will respond with:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMDA...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "computer_code": "ADMIN001",
    "role": "Admin",
    "department": "Management",
    "permissions": ["student.create", "student.read", "dashboard.view", "..."]
  }
}
```
*Depending on the user role, the frontend should redirect to `/dashboard/admin`, `/dashboard/student`, etc.*
