"""
Notification views for Campus Issue Portal.
"""

from bson import ObjectId
from django.shortcuts import render, redirect
from django.http import JsonResponse
from portal.db import get_db, serialize_docs
from portal.auth_helpers import login_required_mongo


@login_required_mongo
def notifications_list(request):
    """View all notifications for the authenticated user."""
    user = request.portal_user
    db = get_db()

    notifications = serialize_docs(
        db.notifications.find({'user_id': user['id']}).sort('created_at', -1)
    )

    return render(request, 'common/notifications.html', {
        'notifications': notifications,
    })


@login_required_mongo
def mark_notification_read(request, notif_id):
    """Marks a single notification as read and optionally redirects to its link."""
    user = request.portal_user
    db = get_db()

    try:
        notif = db.notifications.find_one({'_id': ObjectId(notif_id), 'user_id': user['id']})
        if notif:
            db.notifications.update_one({'_id': ObjectId(notif_id)}, {'$set': {'is_read': True}})
            if notif.get('link'):
                return redirect(notif['link'])
    except Exception:
        pass

    return redirect('notifications_list')


@login_required_mongo
def mark_all_read(request):
    """Marks all user's notifications as read."""
    user = request.portal_user
    db = get_db()
    db.notifications.update_many({'user_id': user['id']}, {'$set': {'is_read': True}})
    return redirect('notifications_list')
