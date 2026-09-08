"""
Middleware for MongoDB user authentication and session management.
"""

from bson import ObjectId
from portal.db import get_db, serialize_doc


class MongoAuthMiddleware:
    """
    Attaches current user document to request.portal_user based on session['user_id'].
    Also caches unread notification count.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_id = request.session.get('user_id')
        request.portal_user = None
        request.unread_notifications_count = 0

        if user_id:
            try:
                db = get_db()
                user = db.users.find_one({'_id': ObjectId(user_id), 'is_active': True})
                if user:
                    request.portal_user = serialize_doc(user)
                    request.unread_notifications_count = db.notifications.count_documents({
                        'user_id': str(user['_id']),
                        'is_read': False
                    })
                else:
                    # User was deactivated or deleted
                    request.session.flush()
            except Exception as e:
                request.portal_user = None

        response = self.get_response(request)
        return response
