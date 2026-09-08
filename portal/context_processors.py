"""
Template context processor for Campus Issue Portal.
Exposes user data, roles, and notifications to all templates.
"""

from portal.db import get_db, serialize_docs


def portal_context(request):
    user = getattr(request, 'portal_user', None)
    unread_count = getattr(request, 'unread_notifications_count', 0)
    recent_notifications = []

    if user:
        try:
            db = get_db()
            recent_notifications = serialize_docs(
                db.notifications.find({'user_id': user['id']}).sort('created_at', -1).limit(5)
            )
        except Exception:
            recent_notifications = []

    return {
        'current_user': user,
        'unread_count': unread_count,
        'recent_notifications': recent_notifications,
        'APP_NAME': 'Campus Issue Portal',
        'YEAR': 2026,
    }
