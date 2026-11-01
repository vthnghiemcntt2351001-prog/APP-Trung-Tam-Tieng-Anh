# Project Structure & Architecture Guide

This project is a Django server-rendered application running on **MySQL 8.0**. The codebase is structured cleanly by business area under the `core` app.

## Top-level layout

```text
.
├── manage.py
├── requirements.txt
├── config/                    # Django settings, root URLs, WSGI and ASGI
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── core/                      # English-center application
    ├── admin.py               # Django Admin registrations with audit protection
    ├── apps.py
    ├── backends.py            # Secure authentication backend (Username / Email)
    ├── blockchain/            # Web3.py smart contract configuration and services
    ├── context_processors.py  # Navigation context processors
    ├── handlers/              # HTTP request handlers grouped by business area
    ├── management/            # Custom Django management commands (setup_roles, seed_data)
    ├── migrations/            # Django schema history for MySQL 8.0
    ├── models.py              # Current model definitions
    ├── permissions.py         # Role-based access control (RBAC) helpers
    ├── services/              # Domain business logic (assessments, class transfers)
    ├── static/core/           # App-owned CSS and JavaScript
    ├── templates/core/        # Django templates grouped by business area
    ├── tests/                 # Unit & integration test package
    ├── urls.py                # Public URL routes mapped to handlers
    └── utils.py               # Shared helpers (e.g., number to Vietnamese words)
```

## Handler modules

- `core/handlers/dashboard.py`: Dashboard metrics, 6-month revenue and student distribution.
- `core/handlers/students.py`: Student profile operations, active/archived filtering, Excel export.
- `core/handlers/academics.py`: Courses, classes, teacher assignments, and class enrollments.
- `core/handlers/class_transfers.py`: Two-step class transfer request, review, approve, and reject.
- `core/handlers/assessments.py`: Dynamic assessment policies, versioning, events, and gradebook.
- `core/handlers/grades.py`: 4-skills grades overview and score entries.
- `core/handlers/tuition.py`: Tuition tracking, debt calculations, receipts, and Excel export.
- `core/handlers/certificates.py`: Certificate listing, search, issuance, and blockchain verification.

All routes in `core/urls.py` point directly to `core.handlers` modules.

## Template layout

```text
core/templates/core/
├── base.html                  # Main layout with SaaS sidebar, topbar, and breadcrumb
├── partials/                  # Shared template partials
├── auth/                      # Login & logout templates
├── dashboard/                 # Analytics & KPI home
├── students/                  # Student list, add, edit, delete
├── academics/
│   ├── courses/               # Course management
│   ├── classes/               # Class roster & detail
│   ├── teachers/              # Instructor records
│   ├── assessments/           # Grading policies & gradebooks
│   └── class_transfers/       # Transfer review workflow
├── grades/                    # Skill scores list, add, edit
├── finance/tuition/           # Tuition list, add, edit, receipt printable
└── certificates/              # Certificate list & blockchain verify
```

Page templates extend `core/base.html`. Page-specific stylesheets mirror the template paths under `core/static/core/css/pages/`; shared styles belong in `core/static/core/css/base.css`.

## Authentication & Role-Based Access Control (RBAC)

The system enforces three primary staff role groups:
- **`Admin`** (`ROLE_ADMIN`): Full system configuration, policy activation, user management.
- **`Học vụ`** (`ROLE_ACADEMIC`): Student admissions, classes, teachers, and grading.
- **`Tài chính`** (`ROLE_FINANCE`): Tuition fee receipts, debt collection, and financial reports.

All protected views are decorated with `@admin_required`, `@academic_required`, `@finance_required`, or `@staff_required` from `core/permissions.py`.
Authentication is handled securely by `core.backends.EmailOrUsernameModelBackend` with strict password hashing validation.

## Automated Testing

Automated test cases reside in `core/tests/`:
- `test_permissions.py`: Verifies RBAC restrictions, 403 blocks for unauthorized staff, and login redirects.
- `test_assessment_service.py`: Verifies assessment calculation, weighting, minimum pass thresholds, and audits.
- `test_class_transfer_service.py`: Verifies two-step class transfer approval and capacity checks.

Run tests using:
```bash
python manage.py test
```
