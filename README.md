# Project Supervision & Monitoring System (PSMS)

Web-based system for supervising student projects with write-up submissions, supervisor reviews, and admin assignment of students to supervisors.

## Features

### Admin
- Create student and supervisor accounts
- Assign students to supervisors
- Manage projects and view all submissions

### Student
- Login with 10-digit matric number (e.g. `2460141001`)
- Submit write-ups as **PDF** or **TXT**
- View supervisor reviews, comments, and approval status
- Download submitted files

### Supervisor
- See all students assigned by admin
- View and download student submissions
- Give reviews: **Approve**, **Revision Required**, **Reject**, or **Noted**
- Add comments and optional rating

## Quick Start

```bash
cd project_supervision_system
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

pip install -r requirements.txt
python scripts/seed.py
python run.py
```

Open **http://127.0.0.1:5000**

## Default Credentials

See `ADMIN_CREDENTIALS.txt`

| Role       | Login                          | Password          |
|------------|--------------------------------|-------------------|
| Admin      | admin@psms.local               | Admin@2024Secure  |
| Student    | 2460141001                     | Student@123       |
| Supervisor | adebayo.okonkwo@university.edu | Supervisor@123    |

## Database

Uses **SQLite** by default (no setup required).

For PostgreSQL, set in `.env`:
```
DATABASE_URL=postgresql://user:pass@localhost:5432/project_supervision
```
Then create the database before running seed.

## Workflow

1. Admin creates accounts and assigns students → supervisors
2. Student uploads PDF/TXT write-up
3. Supervisor reviews, comments, and approves or requests revision
4. Student sees feedback and can resubmit
