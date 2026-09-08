"""
Authentication and Role-Based Access Control (RBAC) helpers.
Provides password hashing, session binding, and view protection decorators.
"""

from functools import wraps
from bson import ObjectId
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from portal.db import get_db, serialize_doc


def hash_password(plain_password: str) -> str:
    """Hash password using PBKDF2 SHA-256."""
    return make_password(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored hash."""
    return check_password(plain_password, hashed_password)


def login_user(request, user_doc):
    """Binds authenticated user to Django session."""
    request.session['user_id'] = str(user_doc['_id'])
    request.session['role'] = user_doc.get('role', 'STUDENT')
    request.session['name'] = user_doc.get('name', '')
    request.session['email'] = user_doc.get('email', '')
    request.session.modified = True


def logout_user(request):
    """Clears user session."""
    request.session.flush()


def get_current_user(request):
    """Returns the authenticated user dict from request, if attached by middleware."""
    return getattr(request, 'portal_user', None)


def login_required_mongo(view_func):
    """Decorator ensuring user is authenticated."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not getattr(request, 'portal_user', None):
            messages.warning(request, "Please log in to access this page.")
            return redirect(f"/login/?next={request.path}")
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(*allowed_roles):
    """Decorator enforcing Role-Based Access Control."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = getattr(request, 'portal_user', None)
            if not user:
                messages.warning(request, "Please log in to continue.")
                return redirect(f"/login/?next={request.path}")

            user_role = user.get('role', '')
            if user_role not in allowed_roles:
                messages.error(request, f"Access denied. This section requires {', '.join(allowed_roles)} privileges.")
                # Redirect to appropriate home based on current role
                if user_role == 'ADMIN':
                    return redirect('admin_dashboard')
                elif user_role == 'FACULTY':
                    return redirect('faculty_dashboard')
                elif user_role == 'STUDENT':
                    return redirect('student_dashboard')
                return redirect('login')

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
