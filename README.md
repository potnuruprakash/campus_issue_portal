# MVGR Campus Issue Portal

[![Live on Render](https://img.shields.io/badge/Render-Live%20Demo-brightgreen?logo=render)](https://campus-issue-portal.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.14-blue?logo=python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0+-092E20?logo=django)](https://www.djangoproject.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb)](https://www.mongodb.com/atlas)

A modern, production-ready, enterprise-grade **Campus Issue Reporting and Resolution Management System** for Maharaj Vijayaram Gajapathi Raj (MVGR) College of Engineering. Built with **Django**, **MongoDB Atlas**, **Bootstrap 5**, and a custom SaaS responsive design system.

🌐 **Production URL:** [https://campus-issue-portal.onrender.com](https://campus-issue-portal.onrender.com)

---

## 🏛️ System Architecture & Highlights

- **Role-Based Access Control (RBAC)**: Strict privilege separation for **Student**, **Faculty**, and **Administrator** roles.
- **Audited 6-Stage Lifecycle**:
  $$\text{Submitted} \longrightarrow \text{Verified} \longrightarrow \text{Assigned} \longrightarrow \text{In Progress} \longrightarrow \text{Resolved} \longrightarrow \text{Closed}$$
- **MongoDB Atlas Cloud Backend**: PyMongo connection pool with automated indexes, TTL/unique constraints, and SSL/TLS encryption (`certifi` + `dnspython`).
- **Production-Grade Security**:
  - Private issue access isolation: Students can only view their own issues.
  - PBKDF2 cryptographically secure password hashing.
  - Server-side validation and file upload size/extension controls.
  - Full CSRF protection configured for HTTPS Render deployments.
  - Environment variable secrets management.
- **Visual Analytics & Reporting**:
  - Live Chart.js analytics for administrative overview (Category distribution, Status breakdown).
  - RFC 4180 CSV export for institutional accreditation and maintenance audits.
- **Interactive Feedback & Audit Trail**:
  - 5-Star rating system with duplicate prevention post-resolution.
  - Immutable audit logs capturing every status transition, assignment, and staff note with timestamps.

---

## ☁️ MongoDB Atlas Cloud Setup

1. **Create a Cluster**:
   - Sign in to [MongoDB Atlas](https://cloud.mongodb.com/) and create a free or dedicated cluster.

2. **Configure Network Access (Whitelist)**:
   - In Atlas, navigate to **Security** $\rightarrow$ **Network Access**.
   - Click **Add IP Address** and choose **Allow Access from Anywhere** (`0.0.0.0/0`).
   - *Note: Render web services use dynamic IP addresses, so `0.0.0.0/0` is required.*

3. **Create Database User**:
   - Navigate to **Security** $\rightarrow$ **Database Access**.
   - Create a database user with **Read and write to any database** privileges.
   - *Tip: If your password contains special characters (`@`, `:`, `#`), make sure they are URL-encoded.*

4. **Copy Connection String**:
   - Click **Connect** $\rightarrow$ **Drivers (Python)**.
   - The connection URI format:
     ```
     mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
     ```

---

## 🚀 Deployment on Render

This repository includes a pre-configured [build.sh](file:///c:/Users/praka/OneDrive/Desktop/New%20folder/campus_issue_portal/build.sh) and production-ready `settings.py` for Render.

### 1. Create Web Service
1. Log in to [Render](https://dashboard.render.com/) and click **New +** $\rightarrow$ **Web Service**.
2. Connect your GitHub repository (`potnuruprakash/campus_issue_portal`).
3. Set the following build and start configurations:
   - **Environment**: `Python 3`
   - **Build Command**:
     ```bash
     chmod +x build.sh && ./build.sh
     ```
   - **Start Command**:
     ```bash
     gunicorn campus_portal.wsgi:application
     ```

### 2. Configure Environment Variables in Render
In your Render Service Dashboard $\rightarrow$ **Environment**, add:

| Environment Variable | Value | Description |
| :--- | :--- | :--- |
| `MONGO_URI` | `mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority` | Your MongoDB Atlas connection URI |
| `MONGO_DB_NAME` | `campus_issue_portal` | Main database name |
| `DEBUG` | `False` | Disables debug mode in production |
| `SECRET_KEY` | *(A long random secret string)* | Production Django secret key |
| `ALLOWED_HOSTS` | `campus-issue-portal.onrender.com` | Allowed hostnames |
| `CSRF_TRUSTED_ORIGINS` | `https://campus-issue-portal.onrender.com` | Required for HTTPS forms |
| `ADMIN_EMAIL` | *(Optional, e.g. `admin@campus.edu`)* | Default admin email if database is empty |
| `ADMIN_PASSWORD` | *(Optional, e.g. `admin123`)* | Default admin password if database is empty |

> [!TIP]
> **Creating or Resetting an Administrator Account:**
> You can create a custom Admin account anytime locally or in Render Shell:
> ```bash
> python manage.py create_admin --email myadmin@campus.edu --password mysecretpassword --name "System Administrator"
> ```
> Or run `python manage.py create_admin` to be prompted interactively.

---

## 💻 Local Development Setup

### 1. Prerequisites
- Python 3.10+ (tested up to Python 3.14)
- Local MongoDB instance (`mongodb://localhost:27017/`) or MongoDB Atlas URI

### 2. Installation & Run
```bash
# Clone the repository
git clone https://github.com/potnuruprakash/campus_issue_portal.git
cd campus_issue_portal

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Copy .env.example to .env and adjust variables as needed:
cp .env.example .env

# Run database migrations for sessions & admin
python manage.py migrate

# Seed categories, accounts, and realistic demo issues
python manage.py seed_data

# Start local development server
python manage.py runserver 127.0.0.1:8000
```

Access the portal locally at:
🔗 **http://127.0.0.1:8000/**

---

## 🔑 Demo Review Accounts (Pre-seeded)

Sign in using your account credentials:

| Role | Email | Password | Scope & Permissions |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@campus.edu` | `admin@123` | Full command center, user management, faculty roster, categories, reports & CSV export |
| **Faculty (CSE)** | `faculty.cse@campus.edu` | `faculty123` | Department queue, verification, assigned issues, status progression, resolution notes |
| **Student** | `alex.student@campus.edu` | `student123` | Report issues with evidence, visual tracking timeline, staff inquiries, 5-star feedback |

---

## 🧪 Automated Test Verification

A test suite verifying all 11 core functional and security behaviors is included:

```bash
python test_comprehensive.py
```

**Verifications Performed:**
- ✅ Public Landing page HTTP 200 OK
- ✅ Student registration & sequential ID generation (`ISS-2026-XXXXX`)
- ✅ Private issue access isolation (anti-tampering check)
- ✅ Role-Based Access Control (RBAC) & unauthorized route denial
- ✅ Faculty dashboard access, verification, and status progression
- ✅ Admin assignment & resolution workflows
- ✅ 5-Star feedback submission & duplicate prevention
- ✅ Complete lifecycle audit trail integrity
- ✅ Administrative reports & RFC 4180 CSV export generation

---

## 📁 Project Structure

```text
campus_issue_portal/
├── build.sh                  # Render deployment automation script
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies (Django, PyMongo, dnspython, certifi, etc.)
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules for secrets and caches
├── test_comprehensive.py     # 11-step end-to-end automated test suite
├── campus_portal/            # Project configuration
│   ├── settings.py           # Production-ready Django settings (WhiteNoise, CSRF, Mongo)
│   ├── urls.py               # Main URL routing & media serving
│   └── wsgi.py               # WSGI entrypoint for Gunicorn
└── portal/                   # Main application package
    ├── db.py                 # PyMongo connection pool & index management
    ├── auth_helpers.py       # Password hashing & session management
    ├── services.py           # Business logic & issue lifecycle orchestration
    ├── views/                # Role-specific controllers (Student, Faculty, Admin, Auth)
    ├── static/               # CSS, JavaScript, and asset files
    └── templates/            # Django responsive HTML5 templates
```
