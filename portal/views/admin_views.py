"""
Admin views for Campus Issue Portal.
Control center for university problem resolution: analytics, full issue management, user administration,
faculty assignment, database-driven category management, and CSV reporting.
"""

import csv
from datetime import datetime, timezone
from bson import ObjectId
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from portal.db import get_db, serialize_doc, serialize_docs
from portal.auth_helpers import login_required_mongo, role_required, hash_password
from portal.services import (
    assign_issue, verify_issue, update_issue_status, add_comment,
    get_admin_analytics, STATUS_CONFIG, PRIORITY_CONFIG, VALID_STATUSES, VALID_PRIORITIES
)
from portal.views.auth_views import DEPARTMENTS


@login_required_mongo
@role_required('ADMIN')
def admin_dashboard(request):
    """Central administrative control center with analytics and charts."""
    analytics = get_admin_analytics()
    db = get_db()

    # Recent 6 issues across the entire campus
    recent_issues = serialize_docs(
        db.issues.find({}).sort('created_at', -1).limit(6)
    )

    # Critical issues requiring immediate attention
    critical_issues = serialize_docs(
        db.issues.find({'priority': 'CRITICAL', 'status': {'$nin': ['Resolved', 'Closed']}}).sort('created_at', -1)
    )

    return render(request, 'admin/dashboard.html', {
        'analytics': analytics,
        'recent_issues': recent_issues,
        'critical_issues': critical_issues,
        'status_config': STATUS_CONFIG,
        'priority_config': PRIORITY_CONFIG,
    })


@login_required_mongo
@role_required('ADMIN')
def admin_issues_list(request):
    """Full issue management table with advanced multi-parameter filtering."""
    db = get_db()
    query = {}

    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
    priority_filter = request.GET.get('priority', '').strip()
    category_filter = request.GET.get('category', '').strip()
    dept_filter = request.GET.get('department', '').strip()

    if search:
        query['$or'] = [
            {'issue_id': {'$regex': search, '$options': 'i'}},
            {'title': {'$regex': search, '$options': 'i'}},
            {'student_name': {'$regex': search, '$options': 'i'}},
            {'assigned_faculty_name': {'$regex': search, '$options': 'i'}},
            {'location': {'$regex': search, '$options': 'i'}},
        ]
    if status_filter:
        query['status'] = status_filter
    if priority_filter:
        query['priority'] = priority_filter
    if category_filter:
        query['category'] = category_filter
    if dept_filter:
        query['department'] = dept_filter

    issues = serialize_docs(db.issues.find(query).sort('created_at', -1))

    # For filter dropdowns and assignment modal
    categories = list(db.categories.find({'is_active': True}).sort('name', 1))
    faculty_list = serialize_docs(db.users.find({'role': 'FACULTY', 'is_active': True}).sort('name', 1))

    return render(request, 'admin/issue_list.html', {
        'issues': issues,
        'categories': categories,
        'departments': DEPARTMENTS,
        'faculty_list': faculty_list,
        'search': search,
        'selected_status': status_filter,
        'selected_priority': priority_filter,
        'selected_category': category_filter,
        'selected_dept': dept_filter,
        'status_config': STATUS_CONFIG,
        'priority_config': PRIORITY_CONFIG,
    })


@login_required_mongo
@role_required('ADMIN')
def admin_issue_detail(request, issue_id):
    """Full administrative control panel for a single issue."""
    db = get_db()
    issue = db.issues.find_one({'issue_id': issue_id})
    if not issue:
        messages.error(request, f"Issue {issue_id} not found.")
        return redirect('admin_issues_list')

    issue_data = serialize_doc(issue)
    comments = serialize_docs(db.comments.find({'issue_id': issue_id}).sort('created_at', 1))
    audit_logs = serialize_docs(db.audit_logs.find({'issue_id': issue_id}).sort('timestamp', 1))
    feedback = db.feedback.find_one({'issue_id': issue_id})
    faculty_list = serialize_docs(db.users.find({'role': 'FACULTY', 'is_active': True}).sort('name', 1))

    return render(request, 'admin/issue_detail.html', {
        'issue': issue_data,
        'comments': comments,
        'audit_logs': audit_logs,
        'feedback': serialize_doc(feedback) if feedback else None,
        'faculty_list': faculty_list,
        'valid_statuses': VALID_STATUSES,
        'valid_priorities': VALID_PRIORITIES,
        'status_config': STATUS_CONFIG,
        'priority_config': PRIORITY_CONFIG,
    })


@login_required_mongo
@role_required('ADMIN')
def admin_assign_faculty(request, issue_id):
    """Assigns or reassigns an issue to a faculty member."""
    if request.method == 'POST':
        faculty_id = request.POST.get('faculty_id', '').strip()
        try:
            assign_issue(request.portal_user, issue_id, faculty_id)
            messages.success(request, f"Issue {issue_id} successfully assigned to faculty.")
        except Exception as e:
            messages.error(request, str(e))
    return redirect('admin_issue_detail', issue_id=issue_id)


@login_required_mongo
@role_required('ADMIN')
def admin_update_issue(request, issue_id):
    """Updates issue status, priority, and resolution notes."""
    if request.method == 'POST':
        new_status = request.POST.get('status', '').strip()
        new_priority = request.POST.get('priority', '').strip()
        notes = request.POST.get('resolution_notes', '').strip()
        try:
            update_issue_status(request.portal_user, issue_id, new_status, notes, new_priority)
            messages.success(request, f"Issue {issue_id} updated.")
        except Exception as e:
            messages.error(request, str(e))
    return redirect('admin_issue_detail', issue_id=issue_id)


@login_required_mongo
@role_required('ADMIN')
def admin_add_comment(request, issue_id):
    """Posts an admin note/comment."""
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        try:
            add_comment(request.portal_user, issue_id, message)
            messages.success(request, "Comment posted.")
        except Exception as e:
            messages.error(request, str(e))
    return redirect('admin_issue_detail', issue_id=issue_id)


@login_required_mongo
@role_required('ADMIN')
def admin_users_list(request):
    """User management view for viewing, filtering, and activating/deactivating accounts."""
    db = get_db()
    query = {}

    search = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role', '').strip()

    if search:
        query['$or'] = [
            {'name': {'$regex': search, '$options': 'i'}},
            {'email': {'$regex': search, '$options': 'i'}},
            {'student_id': {'$regex': search, '$options': 'i'}},
            {'department': {'$regex': search, '$options': 'i'}},
        ]
    if role_filter:
        query['role'] = role_filter

    users = serialize_docs(db.users.find(query).sort('created_at', -1))

    return render(request, 'admin/user_list.html', {
        'users': users,
        'search': search,
        'selected_role': role_filter,
    })


@login_required_mongo
@role_required('ADMIN')
def admin_toggle_user_status(request, user_id):
    """Activates or deactivates a user account."""
    if request.method == 'POST':
        db = get_db()
        user = db.users.find_one({'_id': ObjectId(user_id)})
        if user:
            # Prevent admin deactivating themselves
            if str(user['_id']) == request.portal_user['id']:
                messages.error(request, "You cannot deactivate your own administrative account.")
            else:
                new_state = not user.get('is_active', True)
                db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'is_active': new_state}})
                state_str = "activated" if new_state else "deactivated"
                messages.success(request, f"User '{user.get('name')}' has been {state_str}.")
        else:
            messages.error(request, "User not found.")
    return redirect('admin_users_list')


@login_required_mongo
@role_required('ADMIN')
def admin_faculty_list(request):
    """Faculty management view: add new faculty, update department, view assigned issue counts."""
    db = get_db()

    if request.method == 'POST':
        # Add new faculty member
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        department = request.POST.get('department', '').strip()
        password = request.POST.get('password', '')

        if not name or not email or not department or not password:
            messages.error(request, "All fields are required to create a faculty account.")
        elif len(password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
        elif db.users.find_one({'email': email}):
            messages.error(request, "An account with this email already exists.")
        else:
            now = datetime.now(timezone.utc)
            db.users.insert_one({
                'name': name,
                'email': email,
                'role': 'FACULTY',
                'department': department,
                'password_hash': hash_password(password),
                'is_active': True,
                'created_at': now,
                'updated_at': now
            })
            messages.success(request, f"Faculty account for '{name}' created successfully.")
            return redirect('admin_faculty_list')

    faculty_docs = serialize_docs(db.users.find({'role': 'FACULTY'}).sort('name', 1))

    # Attach issue stats for each faculty
    for f in faculty_docs:
        f['active_issues_count'] = db.issues.count_documents({
            'assigned_faculty_id': f['id'],
            'status': {'$nin': ['Resolved', 'Closed']}
        })
        f['resolved_issues_count'] = db.issues.count_documents({
            'assigned_faculty_id': f['id'],
            'status': {'$in': ['Resolved', 'Closed']}
        })

    return render(request, 'admin/faculty_list.html', {
        'faculty_list': faculty_docs,
        'departments': DEPARTMENTS,
    })


@login_required_mongo
@role_required('ADMIN')
def admin_categories_list(request):
    """Database-driven category management."""
    db = get_db()

    if request.method == 'POST':
        cat_name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        icon = request.POST.get('icon', 'bi-tag').strip()

        if not cat_name:
            messages.error(request, "Category name is required.")
        elif db.categories.find_one({'name': {'$regex': f"^{cat_name}$", '$options': 'i'}}):
            messages.error(request, f"Category '{cat_name}' already exists.")
        else:
            db.categories.insert_one({
                'name': cat_name,
                'description': description,
                'icon': icon,
                'is_active': True,
                'created_at': datetime.now(timezone.utc)
            })
            messages.success(request, f"Category '{cat_name}' added successfully.")
            return redirect('admin_categories_list')

    categories = serialize_docs(db.categories.find({}).sort('name', 1))
    for c in categories:
        c['issues_count'] = db.issues.count_documents({'category': c['name']})

    return render(request, 'admin/category_list.html', {
        'categories': categories,
    })


@login_required_mongo
@role_required('ADMIN')
def admin_toggle_category(request, category_id):
    """Toggles active/inactive state of a category."""
    if request.method == 'POST':
        db = get_db()
        cat = db.categories.find_one({'_id': ObjectId(category_id)})
        if cat:
            new_state = not cat.get('is_active', True)
            db.categories.update_one({'_id': ObjectId(category_id)}, {'$set': {'is_active': new_state}})
            state_str = "activated" if new_state else "deactivated"
            messages.success(request, f"Category '{cat['name']}' has been {state_str}.")
    return redirect('admin_categories_list')


@login_required_mongo
@role_required('ADMIN')
def admin_reports(request):
    """Reports overview with aggregated statistics and CSV export."""
    db = get_db()
    total_issues = db.issues.count_documents({})
    resolved_issues = db.issues.count_documents({'status': {'$in': ['Resolved', 'Closed']}})
    pending_issues = db.issues.count_documents({'status': {'$in': ['Submitted', 'Verified']}})
    in_progress_issues = db.issues.count_documents({'status': {'$in': ['Assigned', 'In Progress']}})

    # Group by category
    by_category = [
        {'name': c['_id'] or 'Uncategorized', 'count': c['count']}
        for c in db.issues.aggregate([
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
    ]

    # Group by department
    by_dept = [
        {'name': d['_id'] or 'General', 'count': d['count']}
        for d in db.issues.aggregate([
            {"$group": {"_id": "$department", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
    ]

    # Group by priority
    by_priority = [
        {'name': p['_id'] or 'MEDIUM', 'count': p['count']}
        for p in db.issues.aggregate([
            {"$group": {"_id": "$priority", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
    ]

    return render(request, 'admin/reports.html', {
        'total_issues': total_issues,
        'resolved_issues': resolved_issues,
        'pending_issues': pending_issues,
        'in_progress_issues': in_progress_issues,
        'by_category': by_category,
        'by_dept': by_dept,
        'by_priority': by_priority,
    })


@login_required_mongo
@role_required('ADMIN')
def export_issues_csv(request):
    """Exports all issues to a clean, formatted CSV document."""
    db = get_db()
    issues = db.issues.find({}).sort('created_at', -1)

    response = HttpResponse(content_type='text/csv')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="campus_issues_report_{timestamp}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Issue ID', 'Title', 'Category', 'Location', 'Priority', 'Status',
        'Student Name', 'Student Email', 'Department', 'Assigned Faculty',
        'Created Date', 'Resolved Date', 'Resolution Notes'
    ])

    for i in issues:
        writer.writerow([
            i.get('issue_id', ''),
            i.get('title', ''),
            i.get('category', ''),
            i.get('location', ''),
            i.get('priority', ''),
            i.get('status', ''),
            i.get('student_name', ''),
            i.get('student_email', ''),
            i.get('department', ''),
            i.get('assigned_faculty_name', 'Unassigned'),
            i.get('created_at', '').strftime('%Y-%m-%d %H:%M') if i.get('created_at') else '',
            i.get('resolved_at', '').strftime('%Y-%m-%d %H:%M') if i.get('resolved_at') else '',
            i.get('resolution_notes', '')
        ])

    return response
