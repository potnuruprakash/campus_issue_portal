"""
Authentication and Profile views for Campus Issue Portal.
"""

from datetime import datetime, timezone
from bson import ObjectId
from django.shortcuts import render, redirect
from django.contrib import messages
from portal.db import get_db, serialize_doc
from portal.auth_helpers import hash_password, verify_password, login_user, logout_user, login_required_mongo

DEPARTMENTS = [
    'Computer Science & Engineering',
    'Electronics & Communication',
    'Mechanical Engineering',
    'Civil Engineering',
    'Electrical Engineering',
    'Information Technology',
    'Business Administration',
    'General Sciences',
]


def landing_page(request):
    """Public landing page highlighting role capabilities and portal benefits."""
    if getattr(request, 'portal_user', None):
        role = request.portal_user.get('role')
        if role == 'ADMIN':
            return redirect('admin_dashboard')
        elif role == 'FACULTY':
            return redirect('faculty_dashboard')
        return redirect('student_dashboard')

    db = get_db()
    total_issues = db.issues.count_documents({})
    resolved_issues = db.issues.count_documents({'status': {'$in': ['Resolved', 'Closed']}})

    return render(request, 'landing.html', {
        'total_issues': total_issues,
        'resolved_issues': resolved_issues,
    })


@login_required_mongo
def admin_entry_view(request):
    """Direct entry point for Administrators via /admin."""
    user = getattr(request, 'portal_user', None)
    if not user or user.get('role') != 'ADMIN':
        messages.error(request, "Access denied. This section requires ADMIN privileges.")
        if user and user.get('role') == 'FACULTY':
            return redirect('faculty_dashboard')
        elif user and user.get('role') == 'STUDENT':
            return redirect('student_dashboard')
        return redirect('/login/?next=/admin/')
    return redirect('admin_dashboard')


@login_required_mongo
def faculty_entry_view(request):
    """Direct entry point for Faculty via /faculity."""
    user = getattr(request, 'portal_user', None)
    if not user or user.get('role') != 'FACULTY':
        messages.error(request, "Access denied. This section requires FACULTY privileges.")
        if user and user.get('role') == 'ADMIN':
            return redirect('admin_dashboard')
        elif user and user.get('role') == 'STUDENT':
            return redirect('student_dashboard')
        return redirect('/login/?next=/faculity/')
    return redirect('faculty_dashboard')


def login_view(request):
    """Handles login for Students, Faculty, and Administrators."""
    if getattr(request, 'portal_user', None):
        role = request.portal_user.get('role')
        if role == 'ADMIN':
            return redirect('admin_dashboard')
        elif role == 'FACULTY':
            return redirect('faculty_dashboard')
        return redirect('student_dashboard')

    if request.method == 'POST':
        login_id = request.POST.get('login_id', '').strip()
        password = request.POST.get('password', '')
        next_url = request.POST.get('next', '')

        if not login_id or not password:
            messages.error(request, "Please provide both your email/student ID and password.")
            return render(request, 'auth/login.html', {'login_id': login_id, 'next': next_url})

        db = get_db()
        # Allow login by email or student_id
        user = db.users.find_one({
            '$or': [
                {'email': login_id.lower()},
                {'student_id': login_id}
            ]
        })

        if not user:
            messages.error(request, "Invalid credentials. Please check your email or password.")
            return render(request, 'auth/login.html', {'login_id': login_id, 'next': next_url})

        if not user.get('is_active', True):
            messages.error(request, "This account is inactive. Please contact the administrator.")
            return render(request, 'auth/login.html', {'login_id': login_id, 'next': next_url})

        if not verify_password(password, user.get('password_hash', '')):
            messages.error(request, "Invalid credentials. Please check your email or password.")
            return render(request, 'auth/login.html', {'login_id': login_id, 'next': next_url})

        # Login success
        login_user(request, user)
        messages.success(request, f"Welcome back, {user.get('name')}!")

        if next_url and next_url.startswith('/'):
            return redirect(next_url)

        role = user.get('role', 'STUDENT')
        if role == 'ADMIN':
            return redirect('admin_dashboard')
        elif role == 'FACULTY':
            return redirect('faculty_dashboard')
        else:
            return redirect('student_dashboard')

    next_url = request.GET.get('next', '')
    return render(request, 'auth/login.html', {'next': next_url})


def register_view(request):
    """Public registration for Students only."""
    if getattr(request, 'portal_user', None):
        return redirect('student_dashboard')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        student_id = request.POST.get('student_id', '').strip().upper()
        email = request.POST.get('email', '').strip().lower()
        department = request.POST.get('department', '').strip()
        year = request.POST.get('year', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # Server-side validation
        if not name or not student_id or not email or not department or not year or not password:
            messages.error(request, "All fields are required.")
            return render(request, 'auth/register.html', {
                'form_data': request.POST,
                'departments': DEPARTMENTS
            })

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return render(request, 'auth/register.html', {
                'form_data': request.POST,
                'departments': DEPARTMENTS
            })

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'auth/register.html', {
                'form_data': request.POST,
                'departments': DEPARTMENTS
            })

        db = get_db()
        # Check if email exists
        if db.users.find_one({'email': email}):
            messages.error(request, "An account with this email address already exists.")
            return render(request, 'auth/register.html', {
                'form_data': request.POST,
                'departments': DEPARTMENTS
            })

        # Check if student ID exists
        if db.users.find_one({'student_id': student_id}):
            messages.error(request, "An account with this Student ID already exists.")
            return render(request, 'auth/register.html', {
                'form_data': request.POST,
                'departments': DEPARTMENTS
            })

        now = datetime.now(timezone.utc)
        user_doc = {
            'name': name,
            'student_id': student_id,
            'email': email,
            'role': 'STUDENT',
            'department': department,
            'year': year,
            'password_hash': hash_password(password),
            'is_active': True,
            'created_at': now,
            'updated_at': now
        }

        result = db.users.insert_one(user_doc)
        user_doc['_id'] = result.inserted_id

        # Automatically log in the registered student
        login_user(request, user_doc)
        messages.success(request, "Account created successfully! Welcome to the Campus Issue Portal.")
        return redirect('student_dashboard')

    return render(request, 'auth/register.html', {
        'departments': DEPARTMENTS
    })


def logout_view(request):
    """Logs out user and redirects to login."""
    logout_user(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('login')


@login_required_mongo
def profile_view(request):
    """User profile viewing and updating."""
    user = request.portal_user
    db = get_db()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        department = request.POST.get('department', '').strip()
        year = request.POST.get('year', '').strip()

        if not name:
            messages.error(request, "Name cannot be empty.")
            return render(request, 'common/profile.html', {'departments': DEPARTMENTS})

        update_fields = {
            'name': name,
            'updated_at': datetime.now(timezone.utc)
        }
        if department:
            update_fields['department'] = department
        if year and user.get('role') == 'STUDENT':
            update_fields['year'] = year

        # Handle password change if provided
        new_password = request.POST.get('new_password', '')
        if new_password:
            if len(new_password) < 6:
                messages.error(request, "New password must be at least 6 characters.")
                return render(request, 'common/profile.html', {'departments': DEPARTMENTS})
            update_fields['password_hash'] = hash_password(new_password)

        db.users.update_one({'_id': ObjectId(user['id'])}, {'$set': update_fields})
        messages.success(request, "Profile updated successfully.")
        return redirect('profile')

    return render(request, 'common/profile.html', {
        'departments': DEPARTMENTS
    })
