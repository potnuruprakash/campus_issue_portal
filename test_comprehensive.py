"""
Comprehensive End-to-End System Test Suite for Campus Issue Portal.
Verifies RBAC, Issue Lifecycle, Private Access Isolation, Feedback, Notifications, and Reports.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus_portal.settings')
django.setup()

from django.test import Client
from portal.db import get_db, serialize_doc
from portal.services import create_issue, generate_issue_id, submit_feedback

def run_tests():
    print("==================================================")
    print("STARTING COMPREHENSIVE CAMPUS PORTAL TEST SUITE")
    print("==================================================")

    db = get_db()
    c = Client()

    # 1. Test Public Landing Page
    res = c.get('/')
    assert res.status_code == 200, f"Landing failed: {res.status_code}"
    print("[PASS] Public Landing page returns 200 OK")

    # 2. Test Student Registration
    test_email = "samuel.test@campus.edu"
    db.users.delete_one({"email": test_email})
    reg_data = {
        "name": "Samuel Test Student",
        "student_id": "STU-2026-TEST99",
        "email": test_email,
        "department": "Computer Science & Engineering",
        "year": "2nd Year",
        "password": "password123",
        "confirm_password": "password123"
    }
    res = c.post('/register/', reg_data)
    assert res.status_code == 302, f"Registration failed: {res.status_code}"
    created_stu = db.users.find_one({"email": test_email})
    assert created_stu is not None
    assert created_stu['role'] == 'STUDENT'
    print(f"[PASS] Student Registration successful. Created user: {created_stu['name']}")

    # 3. Test Student Reporting New Issue
    issue_data = {
        "title": "Broken Hand Dryer in West Wing Restroom",
        "category": "Electricity",
        "location": "Academic Block A, 1st Floor Restroom",
        "priority": "HIGH",
        "description": "The electric hand dryer sensor is defective and does not activate."
    }
    res = c.post('/student/report/', issue_data)
    assert res.status_code == 302, f"Report issue failed: {res.status_code}"
    reported_issue = db.issues.find_one({"student_id": str(created_stu['_id']), "title": issue_data['title']})
    assert reported_issue is not None
    test_issue_id = reported_issue['issue_id']
    assert test_issue_id.startswith("ISS-2026-")
    print(f"[PASS] Issue reported with sequential ID: {test_issue_id}")

    # 4. Test Private Issue Isolation (Security check)
    # Another student (maria) must NOT be able to view Samuel's issue
    maria = db.users.find_one({"email": "maria.student@campus.edu"})
    maria_client = Client()
    m_session = maria_client.session
    m_session['user_id'] = str(maria['_id'])
    m_session['role'] = 'STUDENT'
    m_session.save()
    res = maria_client.get(f'/student/issue/{test_issue_id}/')
    # Should redirect to my_issues with an error message
    assert res.status_code == 302
    assert '/student/issues/' in res.url
    print("[PASS] Security isolation verified: Student cannot access another student's issue")

    # 5. Test Role Authorization Check (Student cannot access admin portal)
    res = c.get('/portal-admin/dashboard/')
    assert res.status_code == 302, f"Security leak! Student accessed admin: {res.status_code}"
    assert '/student/dashboard/' in res.url
    print("[PASS] RBAC protection verified: Student denied access to Admin Dashboard")

    # 6. Test Faculty Login & Issue Verification
    faculty = db.users.find_one({"email": "faculty.cse@campus.edu"})
    fac_client = Client()
    f_session = fac_client.session
    f_session['user_id'] = str(faculty['_id'])
    f_session['role'] = 'FACULTY'
    f_session.save()

    res = fac_client.get('/faculty/dashboard/')
    assert res.status_code == 200
    print("[PASS] Faculty Dashboard accessible for faculty role")

    # Faculty verifies the issue
    res = fac_client.post(f'/faculty/issue/{test_issue_id}/verify/', {"notes": "Verified problem with building maintenance supervisor."})
    assert res.status_code == 302
    updated_iss = db.issues.find_one({"issue_id": test_issue_id})
    assert updated_iss['status'] == 'Verified'
    print(f"[PASS] Faculty verified issue: status is now '{updated_iss['status']}'")

    # 7. Test Admin Assigning Faculty & Changing Status to Resolved
    admin = db.users.find_one({"email": "admin@campus.edu"})
    admin_client = Client()
    a_session = admin_client.session
    a_session['user_id'] = str(admin['_id'])
    a_session['role'] = 'ADMIN'
    a_session.save()

    # Assign to faculty
    res = admin_client.post(f'/portal-admin/issue/{test_issue_id}/assign/', {"faculty_id": str(faculty['_id'])})
    assert res.status_code == 302
    updated_iss = db.issues.find_one({"issue_id": test_issue_id})
    assert updated_iss['assigned_faculty_id'] == str(faculty['_id'])
    print(f"[PASS] Admin assigned issue to faculty: {updated_iss['assigned_faculty_name']}")

    # Update to Resolved with notes
    res = admin_client.post(f'/portal-admin/issue/{test_issue_id}/update/', {
        "status": "Resolved",
        "priority": "HIGH",
        "resolution_notes": "Infrared sensor replaced and calibrated. Fully functional."
    })
    assert res.status_code == 302
    updated_iss = db.issues.find_one({"issue_id": test_issue_id})
    assert updated_iss['status'] == 'Resolved'
    assert updated_iss['resolved_at'] is not None
    print("[PASS] Issue marked as Resolved with official resolution notes and timestamp")

    # 8. Test Student Feedback Submission
    res = c.post(f'/student/issue/{test_issue_id}/feedback/', {
        "rating": "5",
        "comment": "Quick and clean fix! Thank you facilities team."
    })
    assert res.status_code == 302
    feedback_doc = db.feedback.find_one({"issue_id": test_issue_id})
    assert feedback_doc is not None
    assert feedback_doc['rating'] == 5
    print("[PASS] Student 5-Star Feedback submitted and stored")

    # 9. Test Duplicate Feedback Prevention
    res = c.post(f'/student/issue/{test_issue_id}/feedback/', {
        "rating": "4",
        "comment": "Trying duplicate submit."
    })
    feedback_count = db.feedback.count_documents({"issue_id": test_issue_id})
    assert feedback_count == 1
    print("[PASS] Duplicate feedback submission strictly prevented")

    # 10. Test Audit Trail Completeness
    audit_count = db.audit_logs.count_documents({"issue_id": test_issue_id})
    assert audit_count >= 4, f"Expected at least 4 audit logs, found {audit_count}"
    print(f"[PASS] Audit trail recorded {audit_count} lifecycle actions for {test_issue_id}")

    # 11. Test Reports & CSV Export
    res = admin_client.get('/portal-admin/reports/')
    assert res.status_code == 200
    res_csv = admin_client.get('/portal-admin/reports/export/')
    assert res_csv.status_code == 200
    assert 'text/csv' in res_csv['Content-Type']
    assert test_issue_id in res_csv.content.decode('utf-8')
    print("[PASS] CSV export generated valid dataset containing test issue")

    # Cleanup test user
    db.users.delete_one({"email": test_email})
    db.issues.delete_one({"issue_id": test_issue_id})
    db.feedback.delete_one({"issue_id": test_issue_id})
    db.audit_logs.delete_many({"issue_id": test_issue_id})

    print("==================================================")
    print("ALL 11 TEST SUITES PASSED SUCCESSFULLY (100% OK)")
    print("==================================================")

if __name__ == '__main__':
    run_tests()
