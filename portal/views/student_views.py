"""
Student views for Campus Issue Portal.
Allows students to view dashboard, report problems, track lifecycle, comment, and submit feedback.
"""

from bson import ObjectId
from django.shortcuts import render, redirect
from django.contrib import messages
from portal.db import get_db, serialize_doc, serialize_docs
from portal.auth_helpers import login_required_mongo, role_required
from portal.services import (
    create_issue, add_comment, submit_feedback,
    STATUS_CONFIG, PRIORITY_CONFIG
)


@login_required_mongo
@role_required('STUDENT')
def student_dashboard(request):
    """Dedicated dashboard for Students."""
    user = request.portal_user
    db = get_db()
    student_id = user['id']

    # Metrics
    total_issues = db.issues.count_documents({'student_id': student_id})
    pending_issues = db.issues.count_documents({
        'student_id': student_id,
        'status': {'$in': ['Submitted', 'Verified']}
    })
    in_progress_issues = db.issues.count_documents({
        'student_id': student_id,
        'status': {'$in': ['Assigned', 'In Progress']}
    })
    resolved_issues = db.issues.count_documents({
        'student_id': student_id,
        'status': {'$in': ['Resolved', 'Closed']}
    })

    # Recent 5 issues
    recent_issues = serialize_docs(
        db.issues.find({'student_id': student_id}).sort('created_at', -1).limit(5)
    )

    return render(request, 'student/dashboard.html', {
        'total_issues': total_issues,
        'pending_issues': pending_issues,
        'in_progress_issues': in_progress_issues,
        'resolved_issues': resolved_issues,
        'recent_issues': recent_issues,
        'status_config': STATUS_CONFIG,
        'priority_config': PRIORITY_CONFIG,
    })


@login_required_mongo
@role_required('STUDENT')
def report_issue(request):
    """Issue submission form for students."""
    user = request.portal_user
    db = get_db()

    # Database-driven categories
    categories = list(db.categories.find({'is_active': True}).sort('name', 1))
    if not categories:
        # Fallback default categories if not yet seeded
        default_cats = [
            'Classroom', 'Hostel', 'Library', 'Laboratory', 'Electricity',
            'Water', 'Internet/Wi-Fi', 'Transport', 'Cleanliness', 'Security', 'Other'
        ]
        categories = [{'name': c} for c in default_cats]

    if request.method == 'POST':
        try:
            attachment_file = request.FILES.get('attachment')
            new_issue = create_issue(user, request.POST, attachment_file)
            messages.success(
                request,
                f"Issue submitted successfully! Reference ID: {new_issue['issue_id']}."
            )
            return redirect('student_issue_detail', issue_id=new_issue['issue_id'])
        except Exception as e:
            messages.error(request, str(e))
            return render(request, 'student/report_issue.html', {
                'categories': categories,
                'form_data': request.POST,
                'priorities': ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
            })

    return render(request, 'student/report_issue.html', {
        'categories': categories,
        'priorities': ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
    })


@login_required_mongo
@role_required('STUDENT')
def my_issues(request):
    """Lists all issues reported by the current student with filtering & search."""
    user = request.portal_user
    db = get_db()
    student_id = user['id']

    query = {'student_id': student_id}

    # Filters
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
    priority_filter = request.GET.get('priority', '').strip()
    category_filter = request.GET.get('category', '').strip()

    if search:
        query['$or'] = [
            {'issue_id': {'$regex': search, '$options': 'i'}},
            {'title': {'$regex': search, '$options': 'i'}},
            {'location': {'$regex': search, '$options': 'i'}},
        ]
    if status_filter:
        query['status'] = status_filter
    if priority_filter:
        query['priority'] = priority_filter
    if category_filter:
        query['category'] = category_filter

    issues = serialize_docs(
        db.issues.find(query).sort('created_at', -1)
    )

    categories = list(db.categories.find({'is_active': True}).sort('name', 1))

    return render(request, 'student/my_issues.html', {
        'issues': issues,
        'categories': categories,
        'search': search,
        'selected_status': status_filter,
        'selected_priority': priority_filter,
        'selected_category': category_filter,
        'status_config': STATUS_CONFIG,
        'priority_config': PRIORITY_CONFIG,
    })


@login_required_mongo
@role_required('STUDENT')
def student_issue_detail(request, issue_id):
    """Detailed view of an issue for the reporting student."""
    user = request.portal_user
    db = get_db()

    issue = db.issues.find_one({'issue_id': issue_id})
    if not issue:
        messages.error(request, f"Issue '{issue_id}' not found.")
        return redirect('student_my_issues')

    # Security: A student must NEVER access another student's issue
    if str(issue['student_id']) != user['id']:
        messages.error(request, "Access denied. You are not authorized to view issues reported by other students.")
        return redirect('student_my_issues')

    issue_data = serialize_doc(issue)

    # Fetch comments
    comments = serialize_docs(
        db.comments.find({'issue_id': issue_id}).sort('created_at', 1)
    )

    # Fetch audit history / timeline
    audit_logs = serialize_docs(
        db.audit_logs.find({'issue_id': issue_id}).sort('timestamp', 1)
    )

    # Fetch existing feedback if any
    existing_feedback = db.feedback.find_one({'issue_id': issue_id})
    if existing_feedback:
        existing_feedback = serialize_doc(existing_feedback)

    # Lifecycle steps calculation
    steps = [
        {'name': 'Submitted', 'label': 'Issue Submitted', 'icon': 'bi-send'},
        {'name': 'Verified', 'label': 'Issue Verified', 'icon': 'bi-shield-check'},
        {'name': 'Assigned', 'label': 'Assigned', 'icon': 'bi-person-check'},
        {'name': 'In Progress', 'label': 'In Progress', 'icon': 'bi-gear'},
        {'name': 'Resolved', 'label': 'Resolved', 'icon': 'bi-check-circle'},
    ]

    current_status = issue.get('status', 'Submitted')
    current_step_num = STATUS_CONFIG.get(current_status, {}).get('step', 1)

    timeline = []
    for s in steps:
        step_meta = STATUS_CONFIG.get(s['name'], {})
        step_num = step_meta.get('step', 1)
        is_done = current_step_num > step_num or (current_status in ['Resolved', 'Closed'] and step_num <= 5)
        is_current = (current_status == s['name'])
        timeline.append({
            **s,
            'is_done': is_done,
            'is_current': is_current,
            'is_pending': step_num > current_step_num
        })

    return render(request, 'student/issue_detail.html', {
        'issue': issue_data,
        'comments': comments,
        'audit_logs': audit_logs,
        'existing_feedback': existing_feedback,
        'timeline': timeline,
        'status_config': STATUS_CONFIG,
        'priority_config': PRIORITY_CONFIG,
    })


@login_required_mongo
@role_required('STUDENT')
def student_add_comment(request, issue_id):
    """Adds a student comment."""
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        try:
            add_comment(request.portal_user, issue_id, message)
            messages.success(request, "Comment posted successfully.")
        except Exception as e:
            messages.error(request, str(e))
    return redirect('student_issue_detail', issue_id=issue_id)


@login_required_mongo
@role_required('STUDENT')
def student_submit_feedback(request, issue_id):
    """Submits 5-star rating and feedback for a resolved issue."""
    if request.method == 'POST':
        rating = request.POST.get('rating', '5')
        comment = request.POST.get('comment', '').strip()
        try:
            submit_feedback(request.portal_user, issue_id, rating, comment)
            messages.success(request, "Thank you! Your feedback has been recorded.")
        except Exception as e:
            messages.error(request, str(e))
    return redirect('student_issue_detail', issue_id=issue_id)
