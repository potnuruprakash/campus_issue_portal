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
        ensure_baseline_data(_db)
    return _db


def ensure_baseline_data(db):
    """
    Ensures an empty database (e.g. newly connected MongoDB Atlas) has
    at least one active Administrator and baseline categories.
    """
    try:
        from django.contrib.auth.hashers import make_password
        now = datetime.now(timezone.utc)

        # 1. Ensure categories exist if empty
        if db.categories.count_documents({}) == 0:
            categories = [
                {"name": "Classroom", "description": "Audio/visual equipment, projectors, podiums, desks, and air conditioning.", "icon": "bi-easel", "is_active": True, "created_at": now},
                {"name": "Hostel", "description": "Dormitory rooms, common washrooms, plumbing, and laundry facilities.", "icon": "bi-house-door", "is_active": True, "created_at": now},
                {"name": "Library", "description": "Study halls, digital catalog terminals, air flow, and book collection areas.", "icon": "bi-book", "is_active": True, "created_at": now},
                {"name": "Laboratory", "description": "Hardware testing benches, safety hoods, oscilloscopes, and PCs.", "icon": "bi-cpu", "is_active": True, "created_at": now},
                {"name": "Electricity", "description": "Power outages, switchboards, flickering lights, and generator backups.", "icon": "bi-lightning-charge", "is_active": True, "created_at": now},
                {"name": "Water", "description": "Drinking water dispensers, bathroom plumbing, leakages, and overhead tanks.", "icon": "bi-droplet", "is_active": True, "created_at": now},
                {"name": "Internet/Wi-Fi", "description": "Access point drops, campus mesh network, ethernet ports, and proxy.", "icon": "bi-wifi", "is_active": True, "created_at": now},
                {"name": "Transport", "description": "Campus shuttle timings, bus passes, shuttle breakdown, and bicycle bays.", "icon": "bi-bus-front", "is_active": True, "created_at": now},
                {"name": "Cleanliness", "description": "Waste disposal, dustbins, hallway sweeping, and cafeteria sanitation.", "icon": "bi-trash3", "is_active": True, "created_at": now},
                {"name": "Security", "description": "Access gates, ID card scanners, surveillance cameras, and evening patrols.", "icon": "bi-shield-shaded", "is_active": True, "created_at": now},
                {"name": "Other", "description": "General campus queries or unlisted maintenance concerns.", "icon": "bi-tag", "is_active": True, "created_at": now}
            ]
            db.categories.insert_many(categories)

        # 2. Ensure at least one Administrator exists if database has no admins
        if db.users.count_documents({"role": "ADMIN"}) == 0:
            admin_email = os.getenv("ADMIN_EMAIL", "admin@campus.edu").strip().lower()
            admin_password = os.getenv("ADMIN_PASSWORD", "admin@123")
            admin_name = os.getenv("ADMIN_NAME", "Campus Operations Admin").strip()

            db.users.update_one(
                {"email": admin_email},
                {
                    "$setOnInsert": {
                        "name": admin_name,
                        "email": admin_email,
                        "role": "ADMIN",
                        "department": "Campus Operations",
                        "password_hash": make_password(admin_password),
                        "is_active": True,
                        "created_at": now,
                        "updated_at": now,
                    }
                },
                upsert=True
            )
    except Exception as e:
        print(f"Notice during baseline data check: {e}")


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
