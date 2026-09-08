"""
URL configuration for the portal application.
"""

from django.urls import path
from portal.views import auth_views, student_views, faculty_views, admin_views, notification_views

urlpatterns = [
    # Public & Auth
    path('', auth_views.landing_page, name='landing'),
    path('login/', auth_views.login_view, name='login'),
    path('student/login/', auth_views.login_view, name='student_login'),
    path('faculty/login/', auth_views.faculty_login_view, name='faculty_login'),
    path('faculity/login/', auth_views.faculty_login_view),
    path('admin/login/', auth_views.admin_login_view, name='admin_login'),
    path('register/', auth_views.register_view, name='register'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('profile/', auth_views.profile_view, name='profile'),

    # Dedicated Direct Entry Routes
    path('admin/', auth_views.admin_entry_view, name='admin_direct'),
    path('admin', auth_views.admin_entry_view),
    path('faculity/', auth_views.faculty_entry_view, name='faculity_direct'),
    path('faculity', auth_views.faculty_entry_view),
    path('faculty/', auth_views.faculty_entry_view, name='faculty_direct'),
    path('faculty', auth_views.faculty_entry_view),

    # Student routes
    path('student/dashboard/', student_views.student_dashboard, name='student_dashboard'),
    path('student/report/', student_views.report_issue, name='student_report_issue'),
    path('student/issues/', student_views.my_issues, name='student_my_issues'),
    path('student/issue/<str:issue_id>/', student_views.student_issue_detail, name='student_issue_detail'),
    path('student/issue/<str:issue_id>/comment/', student_views.student_add_comment, name='student_add_comment'),
    path('student/issue/<str:issue_id>/feedback/', student_views.student_submit_feedback, name='student_submit_feedback'),

    # Faculty routes
    path('faculty/dashboard/', faculty_views.faculty_dashboard, name='faculty_dashboard'),
    path('faculty/issues/', faculty_views.faculty_issues_list, name='faculty_issues_list'),
    path('faculty/issue/<str:issue_id>/', faculty_views.faculty_issue_detail, name='faculty_issue_detail'),
    path('faculty/issue/<str:issue_id>/verify/', faculty_views.faculty_verify_issue, name='faculty_verify_issue'),
    path('faculty/issue/<str:issue_id>/status/', faculty_views.faculty_update_status, name='faculty_update_status'),
    path('faculty/issue/<str:issue_id>/comment/', faculty_views.faculty_add_comment, name='faculty_add_comment'),

    # Admin routes
    path('portal-admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('portal-admin/issues/', admin_views.admin_issues_list, name='admin_issues_list'),
    path('portal-admin/issue/<str:issue_id>/', admin_views.admin_issue_detail, name='admin_issue_detail'),
    path('portal-admin/issue/<str:issue_id>/assign/', admin_views.admin_assign_faculty, name='admin_assign_faculty'),
    path('portal-admin/issue/<str:issue_id>/update/', admin_views.admin_update_issue, name='admin_update_issue'),
    path('portal-admin/issue/<str:issue_id>/comment/', admin_views.admin_add_comment, name='admin_add_comment'),
    path('portal-admin/users/', admin_views.admin_users_list, name='admin_users_list'),
    path('portal-admin/users/<str:user_id>/toggle/', admin_views.admin_toggle_user_status, name='admin_toggle_user_status'),
    path('portal-admin/faculty/', admin_views.admin_faculty_list, name='admin_faculty_list'),
    path('portal-admin/categories/', admin_views.admin_categories_list, name='admin_categories_list'),
    path('portal-admin/categories/<str:category_id>/toggle/', admin_views.admin_toggle_category, name='admin_toggle_category'),
    path('portal-admin/reports/', admin_views.admin_reports, name='admin_reports'),
    path('portal-admin/reports/export/', admin_views.export_issues_csv, name='export_issues_csv'),

    # Notifications
    path('notifications/', notification_views.notifications_list, name='notifications_list'),
    path('notifications/<str:notif_id>/read/', notification_views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all/', notification_views.mark_all_read, name='mark_all_notifications_read'),
]
