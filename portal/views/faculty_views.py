"""
Faculty views for Campus Issue Portal.
Allows faculty members to view assigned problems, verify issues, update workflow state, and post resolutions.
"""

from bson import ObjectId
from django.shortcuts import render, redirect
from django.contrib import messages
from portal.db import get_db, serialize_doc, serialize_docs
from portal.auth_helpers import login_required_mongo, role_required
from portal.services import (
    verify_issue, update_issue_status, add_comment,
    STATUS_CONFIG, PRIORITY_CONFIG
)


@login_required_mongo
@role_required('FACULTY')
def faculty_dashboard(request):
    """Faculty dashboard displaying assigned tasks and department overviews."""
    user = request.portal_user
    db = get_db()
    faculty_id = user['id']
    faculty_dept = user.get('department', '')

    # Metrics
    assigned_count = db.issues.count_documents({
        'assigned_faculty_id': faculty_id,
        'status': {'$nin': ['Resolved', 'Closed']}
    })
    pending_verification = db.issues.count_documents({
        'status': 'Submitted',
        '$or': [{'department': faculty_dept}, {'department': 'General'}]
    })
    in_progress_count = db.issues.count_documents({
        'assigned_faculty_id': faculty_id,
        'status': 'In Progress'
    })
    resolved_count = db.issues.count_documents({
        'assigned_faculty_id': faculty_id,
        'status': {'$in': ['Resolved', 'Closed']}
    })
    high_priority_count = db.issues.count_documents({
        'assigned_faculty_id': faculty_id,
        'priority': {'$in': ['HIGH', 'CRITICAL']},
        'status': {'$nin': ['Resolved', 'Closed']}
    })

    # Recent assigned issues
    recent_assigned = serialize_docs(
        db.issues.find({'assigned_faculty_id': faculty_id}).sort('created_at', -1).limit(6)
    )

    return render(request, 'faculty/dashboard.html', {
        'assigned_count': assigned_count,
        'pending_verification': pending_verification,
        'in_progress_count': in_progress_count,
        'resolved_count': resolved_count,
        'high_priority_count': high_priority_count,
        'recent_assigned': recent_assigned,
        'status_config': STATUS_CONFIG,
        'priority_config': PRIORITY_CONFIG,
    })


@login_required_mongo
@role_required('FACULTY')
def faculty_issues_list(request):
    """Faculty issue management table with extensive filtering."""
    user = request.portal_user
    db = get_db()
    faculty_id = user['id']

    view_mode = request.GET.get('mode', 'assigned')  # 'assigned' or 'department'
    query = {}

    if view_mode == 'department':
        dept = user.get('department', 'General')
        query['$or'] = [{'department': dept}, {'department': 'General'}]
    else:
        query['assigned_faculty_id'] = faculty_id

    # Filter parameters
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
    priority_filter = request.GET.get('priority', '').strip()
    category_filter = request.GET.get('category', '').strip()

    if search:
        query['$or'] = [
            {'issue_id': {'$regex': search, '$options': 'i'}},
            {'title': {'$regex': search, '$options': 'i'}},
            {'student_name': {'$regex': search, '$options': 'i'}},
            {'location': {'$regex': search, '$options': 'i'}},
        ]
    if status_filter:
        query['status'] = status_filter
    if priority_filter:
        query['priority'] = priority_filter
    if category_filter:
        query['category'] = category_filter

    issues = serialize_docs(db.issues.find(query).sort('created_at', -1))
    categories = list(db.categories.find({'is_active': True}).sort('name', 1))

    return render(request, 'faculty/manage_issues.html', {
        'issues': issues,
        'view_mode': view_mode,
        'categories': categories,
        'search': search,
        'selected_status': status_filter,
        'selected_priority': priority_filter,
        'selected_category': category_filter,
        'status_config': STATUS_CONFIG,
        'priority_config': PRIORITY_CONFIG,
    })


@login_required_mongo
@role_required('FACULTY')
def faculty_issue_detail(request, issue_id):
    """Issue review, verification, and resolution panel for faculty."""
    user = request.portal_user
    db = get_db()

    issue = db.issues.find_one({'issue_id': issue_id})
    if not issue:
        messages.error(request, f"Issue {issue_id} not found.")
        return redirect('faculty_issues_list')

    issue_data = serialize_doc(issue)
    comments = serialize_docs(db.comments.find({'issue_id': issue_id}).sort('created_at', 1))
    audit_logs = serialize_docs(db.audit_logs.find({'issue_id': issue_id}).sort('timestamp', 1))
    feedback = db.feedback.find_one({'issue_id': issue_id})

    return render(request, 'faculty/issue_detail.html', {
        'issue': issue_data,
        'comments': comments,
        'audit_logs': audit_logs,
        'feedback': serialize_doc(feedback) if feedback else None,
        'status_config': STATUS_CONFIG,
        'priority_config': PRIORITY_CONFIG,
    })


@login_required_mongo
@role_required('FACULTY')
def faculty_verify_issue(request, issue_id):
    """Verifies a submitted issue."""
    if request.method == 'POST':
        notes = request.POST.get('notes', '').strip()
        try:
            verify_issue(request.portal_user, issue_id, notes)
            messages.success(request, f"Issue {issue_id} verified successfully.")
        except Exception as e:
            messages.error(request, str(e))
    return redirect('faculty_issue_detail', issue_id=issue_id)


@login_required_mongo
@role_required('FACULTY')
def faculty_update_status(request, issue_id):
    """Updates issue status (e.g. In Progress, Resolved) and adds resolution notes."""
    if request.method == 'POST':
        new_status = request.POST.get('status', '').strip()
        notes = request.POST.get('resolution_notes', '').strip()
        try:
            update_issue_status(request.portal_user, issue_id, new_status, notes)
            messages.success(request, f"Issue {issue_id} updated to '{new_status}'.")
        except Exception as e:
            messages.error(request, str(e))
    return redirect('faculty_issue_detail', issue_id=issue_id)


@login_required_mongo
@role_required('FACULTY')
def faculty_add_comment(request, issue_id):
    """Adds a faculty response or internal update comment."""
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        try:
            add_comment(request.portal_user, issue_id, message)
            messages.success(request, "Comment posted.")
        except Exception as e:
            messages.error(request, str(e))
    return redirect('faculty_issue_detail', issue_id=issue_id)
