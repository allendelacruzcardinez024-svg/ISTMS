# ISTMS — IT Support Ticket Management System (Django)

A premium, responsive Django implementation based on the supplied ISTMS project proposal and UI reference.

## Included
- Login and role-based dashboards
- Employee ticket submission
- My Tickets tracking
- Technician ticket queue
- Ticket details and update timeline
- Ticket assignment and status updates
- Admin/Manager dashboard
- Reports and charts
- User Management
- Knowledge Base
- Profile and Settings
- Responsive premium UI with separate CSS and JavaScript

## Requirements
- Python 3.11+ recommended
- Django 5.2+
- No external database is required for the demo; SQLite is configured by default.

## Run on Windows

1. Open Command Prompt / PowerShell in this folder.
2. Create a virtual environment:
   `python -m venv venv`
3. Activate it:
   `venv\Scripts\activate`
4. Install Django:
   `pip install -r requirements.txt`
5. Create the database:
   `python manage.py migrate`
6. Create demo data:
   `python manage.py seed_demo`
7. Start the server:
   `python manage.py runserver`
8. Open:
   `http://127.0.0.1:8000/`

## Demo accounts
- Employee: `employee` / `password123`
- Technician: `technician` / `password123`
- Admin: `admin` / `password123`
- Manager: `manager` / `password123`

## Production notes
Change SECRET_KEY, DEBUG, ALLOWED_HOSTS, database settings, upload handling, email settings, and security settings before deployment.
