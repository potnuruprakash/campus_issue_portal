"""
Business logic service layer for Campus Issue Portal.
Handles issue generation, workflow status transitions, audit logs, notifications, and analytics.
"""

import os
from datetime import datetime, timezone
from bson import ObjectId
from django.conf import settings
from django.core.files.storage import default_storage
from portal.db import get_db, serialize_doc, serialize_docs

VALID_STATUSES = ['Submitted', 'Verified', 'Assigned', 'In Progress', 'Resolved', 'Closed']
VALID_PRIORITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

# Status colors & badge classes
STATUS_CONFIG = {
    'Submitted': {'color': 'primary', 'badge': 'bg-primary', 'hex': '#0d6efd', 'step': 1},
    'Verified': {'color': 'purple', 'badge': 'bg-purple', 'hex': '#6f42c1', 'step': 2},
    'Assigned': {'color': 'warning', 'badge': 'bg-warning text-dark', 'hex': '#fd7e14', 'step': 3},
    'In Progress': {'color': 'info', 'badge': 'bg-info text-dark', 'hex': '#0dcaf0', 'step': 4},
    'Resolved': {'color': 'success', 'badge': 'bg-success', 'hex': '#198754', 'step': 5},
    'Closed': {'color': 'secondary', 'badge': 'bg-secondary', 'hex': '#6c757d', 'step': 6},
}

PRIORITY_CONFIG = {
    'LOW': {'badge': 'bg-secondary-subtle text-secondary border border-secondary', 'level': 1},
    'MEDIUM': {'badge': 'bg-primary-subtle text-primary border border-primary', 'level': 2},
    'HIGH': {'badge': 'bg-warning-subtle text-warning-emphasis border border-warning', 'level': 3},
    'CRITICAL': {'badge': 'bg-danger text-white border border-danger shadow-sm pulse-danger', 'level': 4},
}


def generate_issue_id() -> str:
    """Generates unique sequential Issue ID in the format ISS-2026-XXXXX."""
    db = get_db()
    current_year = datetime.now().year
    count = db.issues.count_documents({}) + 1
    # Check uniqueness
    candidate = f"ISS-{current_year}-{count:05d}"
    while db.issues.find_one({'issue_id': candidate}):
        count += 1
        candidate = f"ISS-{current_year}-{count:05d}"
    return candidate


def log_audit(issue_id: str, action: str, performed_by: dict, details: str = ""):
    """Logs an action to the issue history / audit trail."""
    db = get_db()
    db.audit_logs.insert_one({
        'issue_id': issue_id,
        'action': action,
        'performed_by_id': str(performed_by.get('id', performed_by.get('_id', ''))),
        'performed_by_name': performed_by.get('name', 'System'),
        'performed_by_role': performed_by.get('role', 'SYSTEM'),
        'details': details,
        'timestamp': datetime.now(timezone.utc)
    })


def create_notification(user_id: str, title: str, message: str, link: str = "", notif_type: str = "info"):
    """Dispatches in-app notification to a user."""
    db = get_db()
    db.notifications.insert_one({
        'user_id': str(user_id),
        'title': title,
        'message': message,
        'link': link,
        'is_read': False,
        'type': notif_type,
        'created_at': datetime.now(timezone.utc)
    })


def notify_admins(title: str, message: str, link: str = "", notif_type: str = "warning"):
    """Broadcasts notification to all active administrators."""
    db = get_db()
    admins = db.users.find({'role': 'ADMIN', 'is_active': True})
    for admin in admins:
        create_notification(str(admin['_id']), title, message, link, notif_type)


def create_issue(student_user: dict, data: dict, attachment_file=None):
    """
    Creates a new issue reported by a student.
    Validates required fields, saves attachment, writes to DB, logs audit, and sends notifications.
    """
    db = get_db()

    title = data.get('title', '').strip()
    category = data.get('category', '').strip()
    location = data.get('location', '').strip()
    description = data.get('description', '').strip()
    priority = data.get('priority', 'MEDIUM').upper()

    if not title:
        raise ValueError("Please provide a concise issue title.")
    if not category:
        raise ValueError("Please select an issue category.")
    if not location:
        raise ValueError("Location is required.")
    if not description:
        raise ValueError("Please provide a detailed description.")
    if priority not in VALID_PRIORITIES:
        priority = 'MEDIUM'

    attachment_name = ""
    attachment_path = ""

    if attachment_file:
        ext = os.path.splitext(attachment_file.name)[1].lower()
        if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            raise ValueError(f"Unsupported file format '{ext}'. Allowed: {', '.join(settings.ALLOWED_UPLOAD_EXTENSIONS)}")
        if attachment_file.size > settings.MAX_UPLOAD_SIZE:
            raise ValueError("File size exceeds 5MB limit.")

        filename = f"issue_{datetime.now().strftime('%Y%m%d%H%M%S')}_{attachment_file.name}"
        saved_path = default_storage.save(f"attachments/{filename}", attachment_file)
        attachment_name = attachment_file.name
        attachment_path = default_storage.url(saved_path)

    issue_id = generate_issue_id()
    now = datetime.now(timezone.utc)

    issue_doc = {
        'issue_id': issue_id,
        'title': title,
        'category': category,
        'location': location,
        'description': description,
        'priority': priority,
        'status': 'Submitted',
        'student_id': str(student_user.get('id', student_user.get('_id'))),
        'student_name': student_user.get('name', ''),
        'student_email': student_user.get('email', ''),
        'department': student_user.get('department', 'General'),
        'assigned_faculty_id': None,
        'assigned_faculty_name': None,
        'attachment_name': attachment_name,
        'attachment_path': attachment_path,
        'resolution_notes': '',
        'created_at': now,
        'updated_at': now,
        'resolved_at': None,
        'closed_at': None
    }

    result = db.issues.insert_one(issue_doc)
    issue_doc['_id'] = result.inserted_id

    # Log audit entry
    log_audit(issue_id, "Issue Submitted", student_user, f"Priority: {priority}, Location: {location}")

    # Notify student
    create_notification(
        user_id=student_user['id'],
        title="Issue Submitted Successfully",
        message=f"Your issue '{title}' has been registered with ID {issue_id}.",
        link=f"/student/issue/{issue_id}/",
        notif_type="success"
    )

    # Notify Admins
    admin_notif_type = "danger" if priority == 'CRITICAL' else "info"
    notify_admins(
        title=f"New Issue Reported [{priority}]: {issue_id}",
        message=f"Student {student_user.get('name')} reported '{title}' in {location}.",
        link=f"/admin/issues/?search={issue_id}",
        notif_type=admin_notif_type
    )

    return serialize_doc(issue_doc)


def verify_issue(user: dict, issue_id: str, notes: str = ""):
    """Verifies a submitted issue."""
    db = get_db()
    issue = db.issues.find_one({'issue_id': issue_id})
    if not issue:
        raise ValueError(f"Issue {issue_id} not found.")

    now = datetime.now(timezone.utc)
    db.issues.update_one(
        {'issue_id': issue_id},
        {'$set': {'status': 'Verified', 'updated_at': now}}
    )

    log_audit(issue_id, "Issue Verified", user, notes or "Verified by staff member")

    # Notify student
    create_notification(
        user_id=issue['student_id'],
        title="Issue Verified",
        message=f"Your issue {issue_id} has been verified and queued for assignment.",
        link=f"/student/issue/{issue_id}/",
        notif_type="info"
    )


def assign_issue(user: dict, issue_id: str, faculty_id: str):
    """Assigns an issue to a faculty member."""
    db = get_db()
    issue = db.issues.find_one({'issue_id': issue_id})
    if not issue:
        raise ValueError(f"Issue {issue_id} not found.")

    faculty = db.users.find_one({'_id': ObjectId(faculty_id), 'role': 'FACULTY'})
    if not faculty:
        raise ValueError("Selected faculty member was not found.")

    now = datetime.now(timezone.utc)
    new_status = 'Assigned' if issue['status'] in ['Submitted', 'Verified'] else issue['status']

    db.issues.update_one(
        {'issue_id': issue_id},
        {
            '$set': {
                'assigned_faculty_id': str(faculty['_id']),
                'assigned_faculty_name': faculty.get('name', 'Faculty'),
                'status': new_status,
                'updated_at': now
            }
        }
    )

    log_audit(issue_id, "Assigned to Faculty", user, f"Assigned to {faculty.get('name')} ({faculty.get('department')})")

    # Notify Faculty
    create_notification(
        user_id=str(faculty['_id']),
        title=f"New Assigned Issue: {issue_id}",
        message=f"You have been assigned to issue '{issue.get('title')}' [{issue.get('priority')}].",
        link=f"/faculty/issue/{issue_id}/",
        notif_type="warning" if issue.get('priority') in ['HIGH', 'CRITICAL'] else "info"
    )

    # Notify Student
    create_notification(
        user_id=issue['student_id'],
        title="Issue Assigned",
        message=f"Your issue {issue_id} has been assigned to {faculty.get('name')}.",
        link=f"/student/issue/{issue_id}/",
        notif_type="info"
    )


def update_issue_status(user: dict, issue_id: str, new_status: str, notes: str = "", new_priority: str = None):
    """Updates the status and/or priority of an issue, records resolution timestamp if resolved."""
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{new_status}'.")

    db = get_db()
    issue = db.issues.find_one({'issue_id': issue_id})
    if not issue:
        raise ValueError(f"Issue {issue_id} not found.")

    now = datetime.now(timezone.utc)
    update_fields = {
        'status': new_status,
        'updated_at': now
    }

    if notes:
        update_fields['resolution_notes'] = notes

    if new_priority and new_priority in VALID_PRIORITIES:
        update_fields['priority'] = new_priority

    if new_status == 'Resolved' and not issue.get('resolved_at'):
        update_fields['resolved_at'] = now
    elif new_status == 'Closed' and not issue.get('closed_at'):
        update_fields['closed_at'] = now

    db.issues.update_one({'issue_id': issue_id}, {'$set': update_fields})

    detail_msg = f"Status updated to '{new_status}'."
    if notes:
        detail_msg += f" Note: {notes}"
    if new_priority and new_priority != issue.get('priority'):
        detail_msg += f" Priority changed to {new_priority}."

    log_audit(issue_id, f"Status Changed to {new_status}", user, detail_msg)

    # Notify student
    create_notification(
        user_id=issue['student_id'],
        title=f"Issue Status Update: {new_status}",
        message=f"Your issue {issue_id} is now '{new_status}'. {notes}",
        link=f"/student/issue/{issue_id}/",
        notif_type="success" if new_status == 'Resolved' else "info"
    )


def add_comment(user: dict, issue_id: str, message: str):
    """Adds a comment to an issue and alerts opposing parties."""
    message = message.strip()
    if not message:
        raise ValueError("Comment cannot be empty.")

    db = get_db()
    issue = db.issues.find_one({'issue_id': issue_id})
    if not issue:
        raise ValueError("Issue not found.")

    now = datetime.now(timezone.utc)
    comment_doc = {
        'issue_id': issue_id,
        'user_id': str(user.get('id', user.get('_id'))),
        'user_name': user.get('name', 'Anonymous'),
        'user_role': user.get('role', 'STUDENT'),
        'message': message,
        'created_at': now
    }
    db.comments.insert_one(comment_doc)

    log_audit(issue_id, "Comment Added", user, f"Added comment: {message[:60]}...")

    # Notifications
    user_id_str = str(user.get('id', user.get('_id')))
    # If commenter is student, notify assigned faculty or admin
    if user.get('role') == 'STUDENT':
        if issue.get('assigned_faculty_id'):
            create_notification(
                user_id=issue['assigned_faculty_id'],
                title=f"New Comment on {issue_id}",
                message=f"Student {user.get('name')} commented: {message[:80]}...",
                link=f"/faculty/issue/{issue_id}/",
                notif_type="info"
            )
    else:
        # If staff commented, notify student
        if issue.get('student_id') != user_id_str:
            create_notification(
                user_id=issue['student_id'],
                title=f"Staff Response on {issue_id}",
                message=f"{user.get('name')} ({user.get('role')}): {message[:80]}...",
                link=f"/student/issue/{issue_id}/",
                notif_type="info"
            )


def submit_feedback(student_user: dict, issue_id: str, rating: int, comment: str = ""):
    """Submits student feedback after an issue is resolved."""
    db = get_db()
    issue = db.issues.find_one({'issue_id': issue_id})
    if not issue:
        raise ValueError("Issue not found.")

    if issue['status'] not in ['Resolved', 'Closed']:
        raise ValueError("Feedback can only be submitted after the issue is resolved.")

    if str(issue['student_id']) != str(student_user.get('id', student_user.get('_id'))):
        raise ValueError("You can only submit feedback for your own reported issues.")

    existing = db.feedback.find_one({'issue_id': issue_id})
    if existing:
        raise ValueError("Feedback has already been submitted for this issue.")

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError()
    except Exception:
        raise ValueError("Rating must be an integer between 1 and 5.")

    now = datetime.now(timezone.utc)
    db.feedback.insert_one({
        'issue_id': issue_id,
        'student_id': str(student_user.get('id', student_user.get('_id'))),
        'student_name': student_user.get('name', ''),
        'rating': rating,
        'comment': comment.strip(),
        'created_at': now
    })

    log_audit(issue_id, "Student Submitted Feedback", student_user, f"Rating: {rating}/5 stars. Feedback: {comment[:50]}")


def get_admin_analytics() -> dict:
    """Computes comprehensive analytics and metrics for the Admin dashboard."""
    db = get_db()

    total_issues = db.issues.count_documents({})
    submitted_count = db.issues.count_documents({'status': 'Submitted'})
    verified_count = db.issues.count_documents({'status': 'Verified'})
    pending_count = submitted_count + verified_count
    in_progress_count = db.issues.count_documents({'status': {'$in': ['Assigned', 'In Progress']}})
    resolved_count = db.issues.count_documents({'status': {'$in': ['Resolved', 'Closed']}})
    critical_count = db.issues.count_documents({'priority': 'CRITICAL', 'status': {'$nin': ['Resolved', 'Closed']}})

    # Category breakdown
    cat_pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    categories_agg = list(db.issues.aggregate(cat_pipeline))
    cat_labels = [c['_id'] or 'Uncategorized' for c in categories_agg]
    cat_counts = [c['count'] for c in categories_agg]

    # Status breakdown
    status_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_agg = list(db.issues.aggregate(status_pipeline))
    status_map = {s['_id']: s['count'] for s in status_agg}
    status_labels = ['Submitted', 'Verified', 'Assigned', 'In Progress', 'Resolved', 'Closed']
    status_counts = [status_map.get(s, 0) for s in status_labels]

    # Priority breakdown
    priority_pipeline = [
        {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
    ]
    priority_agg = list(db.issues.aggregate(priority_pipeline))
    priority_map = {p['_id']: p['count'] for p in priority_agg}

    # Total Users counts
    total_students = db.users.count_documents({'role': 'STUDENT'})
    total_faculty = db.users.count_documents({'role': 'FACULTY'})

    return {
        'total_issues': total_issues,
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'resolved_count': resolved_count,
        'critical_count': critical_count,
        'total_students': total_students,
        'total_faculty': total_faculty,
        'cat_labels': cat_labels,
        'cat_counts': cat_counts,
        'status_labels': status_labels,
        'status_counts': status_counts,
        'priority_map': priority_map
    }
