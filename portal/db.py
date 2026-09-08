"""
MongoDB Connection and Database Management for Campus Issue Portal.
Uses PyMongo client with connection pooling, automatic index creation, and safe serialization.
"""

import os
from datetime import datetime, timezone
from bson import ObjectId
from pymongo import MongoClient, ASCENDING, DESCENDING
from django.conf import settings

_client = None
_db = None


def get_mongo_client():
    global _client
    if _client is None:
        uri = getattr(settings, 'MONGO_URI', os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
        client_kwargs = {
            "serverSelectionTimeoutMS": 5000,
            "connectTimeoutMS": 5000,
            "maxPoolSize": 50,
            "minPoolSize": 5,
        }
        # If connecting to MongoDB Atlas (srv) or TLS-enabled Mongo, provide certifi CA bundle
        if "mongodb+srv://" in uri or "ssl=true" in uri.lower() or "tls=true" in uri.lower():
            try:
                import certifi
                client_kwargs["tlsCAFile"] = certifi.where()
            except Exception:
                pass
        _client = MongoClient(uri, **client_kwargs)
    return _client


def get_db():
    global _db
    if _db is None:
        client = get_mongo_client()
        db_name = getattr(settings, 'MONGO_DB_NAME', os.getenv('MONGO_DB_NAME', 'campus_issue_portal'))
        _db = client[db_name]
        init_db_indexes(_db)
    return _db


def init_db_indexes(db):
    """
    Ensure all collections have optimal indexes for performance, uniqueness, and filtering.
    """
    try:
        # Users collection
        db.users.create_index([("email", ASCENDING)], unique=True)
        db.users.create_index([("role", ASCENDING)])
        db.users.create_index([("student_id", ASCENDING)], sparse=True)

        # Issues collection
        db.issues.create_index([("issue_id", ASCENDING)], unique=True)
        db.issues.create_index([("student_id", ASCENDING)])
        db.issues.create_index([("assigned_faculty_id", ASCENDING)])
        db.issues.create_index([("status", ASCENDING)])
        db.issues.create_index([("priority", ASCENDING)])
        db.issues.create_index([("category", ASCENDING)])
        db.issues.create_index([("created_at", DESCENDING)])

        # Comments collection
        db.comments.create_index([("issue_id", ASCENDING), ("created_at", ASCENDING)])

        # Notifications collection
        db.notifications.create_index([("user_id", ASCENDING), ("is_read", ASCENDING), ("created_at", DESCENDING)])

        # Feedback collection (unique per issue to prevent duplicate submissions)
        db.feedback.create_index([("issue_id", ASCENDING)], unique=True)

        # Audit logs / History
        db.audit_logs.create_index([("issue_id", ASCENDING), ("timestamp", ASCENDING)])

        # Categories collection
        db.categories.create_index([("name", ASCENDING)], unique=True)
    except Exception as e:
        # Avoid crashing during initialization if indexes already exist or during offline checks
        print(f"Warning initializing Mongo indexes: {e}")


def serialize_doc(doc):
    """
    Converts MongoDB document ObjectId and datetimes to JSON/template-friendly formats.
    """
    if not doc:
        return None
    doc = dict(doc)
    if '_id' in doc:
        doc['id'] = str(doc['_id'])
        doc['_id'] = str(doc['_id'])
    return doc


def serialize_docs(docs):
    return [serialize_doc(d) for d in docs]
