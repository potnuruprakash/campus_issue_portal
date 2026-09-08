# Campus Issue Portal

A professional, production-ready, enterprise-grade **Campus Issue Reporting and Resolution Management System** for universities and colleges. Built with **Django**, **MongoDB**, **Bootstrap 5**, and a custom SaaS design system.

---

## 🏛️ System Architecture & Highlights

- **Full Role-Based Access Control (RBAC)**: Strict privileges separating **Student**, **Faculty**, and **Administrator** roles.
- **Audited 6-Stage Lifecycle**:
  $$\text{Submitted} \longrightarrow \text{Verified} \longrightarrow \text{Assigned} \longrightarrow \text{In Progress} \longrightarrow \text{Resolved} \longrightarrow \text{Closed}$$
- **Native MongoDB Backend**: PyMongo connection pool with indexes, geospatial/category aggregations, and high concurrency.
- **Enterprise Security**:
  - Private issue access isolation: Students can only view their own issues.
  - PBKDF2 cryptographically secure password hashing.
  - Server-side validation and file upload size/extension controls.
  - CSRF protection on all mutating actions.
  - Environment variable secrets management.
- **Visual Analytics & Reporting**:
  - Live Chart.js analytics for administrative overview (Category distribution, Status breakdown).
  - RFC 4180 CSV export for institutional accreditation and maintenance audits.
- **Interactive Feedback & Audit Trail**:
  - 5-Star rating system with duplicate prevention post-resolution.
  - Immutable audit logs capturing every status transition, assignment, and staff note with timestamps.

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Running MongoDB Server instance (`mongodb://localhost:27017/`)

### 2. Installation & Setup
```bash
# Navigate to project directory
cd campus_issue_portal

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (a pre-configured .env is included)
# Copy .env.example if needed:
cp .env.example .env

# Run database migrations for sessions
python manage.py migrate

# Seed categories, accounts, and realistic demo issues
python manage.py seed_data

# Start development server
python manage.py runserver 127.0.0.1:8000
```

Access the application in your browser:
🔗 **http://127.0.0.1:8000/**

---

## 🔑 Demo Review Accounts (Pre-seeded)

Use the 1-click **Quick Demo Fill** buttons on `/login/` or enter credentials manually:

| Role | Email | Password | Scope & Permissions |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@campus.edu` | `admin123` | Full command center, user management, faculty roster, categories, reports & CSV export |
| **Faculty (CSE)** | `faculty.cse@campus.edu` | `faculty123` | Department queue, verification, assigned issues, status progression, resolution notes |
| **Student** | `alex.student@campus.edu` | `student123` | Report issues with evidence, visual tracking timeline, staff inquiries, 5-star feedback |

---

## 🧪 Automated Test Verification

A test suite verifying all 11 core functional and security behaviors is included:
```bash
python test_comprehensive.py
```
Outputs:
- Landing page HTTP 200 OK
- Student registration & sequential ID generation (`ISS-2026-XXXXX`)
- Private issue access isolation (anti-tampering check)
- Role protection & denial for unauthorized endpoints
- Faculty verification and status progression
- Admin assignment & resolution
- 5-Star feedback submission & duplicate prevention
- Audit trail integrity
- CSV export generation
