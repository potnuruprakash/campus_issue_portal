"""
Django Management Command to Seed Realistic Campus Data.
Usage: python manage.py seed_data
"""

from datetime import datetime, timezone, timedelta
from django.core.management.base import BaseCommand
from portal.db import get_db
from portal.auth_helpers import hash_password

CATEGORIES = [
    {"name": "Classroom", "description": "Audio/visual equipment, projectors, podiums, desks, and air conditioning.", "icon": "bi-easel"},
    {"name": "Hostel", "description": "Dormitory rooms, common washrooms, plumbing, and laundry facilities.", "icon": "bi-house-door"},
    {"name": "Library", "description": "Study halls, digital catalog terminals, air flow, and book collection areas.", "icon": "bi-book"},
    {"name": "Laboratory", "description": "Hardware testing benches, safety hoods, oscilloscopes, and PCs.", "icon": "bi-cpu"},
    {"name": "Electricity", "description": "Power outages, switchboards, flickering lights, and generator backups.", "icon": "bi-lightning-charge"},
    {"name": "Water", "description": "Drinking water dispensers, bathroom plumbing, leakages, and overhead tanks.", "icon": "bi-droplet"},
    {"name": "Internet/Wi-Fi", "description": "Access point drops, campus mesh network, ethernet ports, and proxy.", "icon": "bi-wifi"},
    {"name": "Transport", "description": "Campus shuttle timings, bus passes, shuttle breakdown, and bicycle bays.", "icon": "bi-bus-front"},
    {"name": "Cleanliness", "description": "Waste disposal, dustbins, hallway sweeping, and cafeteria sanitation.", "icon": "bi-trash3"},
    {"name": "Security", "description": "Access gates, ID card scanners, surveillance cameras, and evening patrols.", "icon": "bi-shield-shaded"},
    {"name": "Other", "description": "General campus queries or unlisted maintenance concerns.", "icon": "bi-tag"}
]


class Command(BaseCommand):
    help = "Seeds initial categories, sample users for each role, and realistic test issues."

    def handle(self, *args, **options):
        db = get_db()
        self.stdout.write("Initializing Campus Issue Portal seed data...")

        # 1. Categories
        for cat in CATEGORIES:
            db.categories.update_one(
                {"name": cat["name"]},
                {"$setOnInsert": {**cat, "is_active": True, "created_at": datetime.now(timezone.utc)}},
                upsert=True
            )
        self.stdout.write(self.style.SUCCESS(f"[OK] {len(CATEGORIES)} categories verified."))

        # 2. Users (Admin, Faculty, Students)
        now = datetime.now(timezone.utc)
        users = [
            {
                "name": "Dr. Sarah Jenkins",
                "email": "admin@campus.edu",
                "role": "ADMIN",
                "department": "Campus Operations",
                "password_hash": hash_password("admin123"),
                "is_active": True,
                "created_at": now,
                "updated_at": now
            },
            {
                "name": "Prof. Alan Vance",
                "email": "faculty.cse@campus.edu",
                "role": "FACULTY",
                "department": "Computer Science & Engineering",
                "password_hash": hash_password("faculty123"),
                "is_active": True,
                "created_at": now,
                "updated_at": now
            },
            {
                "name": "Dr. Marcus Bell",
                "email": "faculty.mech@campus.edu",
                "role": "FACULTY",
                "department": "Mechanical Engineering",
                "password_hash": hash_password("faculty123"),
                "is_active": True,
                "created_at": now,
                "updated_at": now
            },
            {
                "name": "Prof. Priya Nair",
                "email": "faculty.ece@campus.edu",
                "role": "FACULTY",
                "department": "Electronics & Communication",
                "password_hash": hash_password("faculty123"),
                "is_active": True,
                "created_at": now,
                "updated_at": now
            },
            {
                "name": "Alex Johnson",
                "email": "alex.student@campus.edu",
                "student_id": "STU-2026-00101",
                "role": "STUDENT",
                "department": "Computer Science & Engineering",
                "year": "3rd Year",
                "password_hash": hash_password("student123"),
                "is_active": True,
                "created_at": now,
                "updated_at": now
            },
            {
                "name": "Maria Garcia",
                "email": "maria.student@campus.edu",
                "student_id": "STU-2026-00102",
                "role": "STUDENT",
                "department": "Electronics & Communication",
                "year": "2nd Year",
                "password_hash": hash_password("student123"),
                "is_active": True,
                "created_at": now,
                "updated_at": now
            },
            {
                "name": "David Kim",
                "email": "david.student@campus.edu",
                "student_id": "STU-2026-00103",
                "role": "STUDENT",
                "department": "Mechanical Engineering",
                "year": "4th Year",
                "password_hash": hash_password("student123"),
                "is_active": True,
                "created_at": now,
                "updated_at": now
            }
        ]

        user_map = {}
        for u in users:
            existing = db.users.find_one({"email": u["email"]})
            if not existing:
                res = db.users.insert_one(u)
                u["_id"] = res.inserted_id
                user_map[u["email"]] = u
            else:
                user_map[u["email"]] = existing

        self.stdout.write(self.style.SUCCESS("[OK] Admin, Faculty, and Student accounts verified."))

        # 3. Seed Realistic Issues
        alex = user_map["alex.student@campus.edu"]
        maria = user_map["maria.student@campus.edu"]
        david = user_map["david.student@campus.edu"]
        prof_vance = user_map["faculty.cse@campus.edu"]
        dr_bell = user_map["faculty.mech@campus.edu"]
        admin = user_map["admin@campus.edu"]

        issues = [
            {
                "issue_id": "ISS-2026-00124",
                "title": "Wi-Fi connectivity problem in CSE block",
                "category": "Internet/Wi-Fi",
                "location": "CSE Building, 2nd Floor Labs",
                "description": "The enterprise wireless access points in Labs 201 and 203 keep dropping connections during practical sessions. Students are unable to access cloud IDEs or push code to university git repositories.",
                "priority": "CRITICAL",
                "status": "In Progress",
                "student_id": str(alex["_id"]),
                "student_name": alex["name"],
                "student_email": alex["email"],
                "department": alex["department"],
                "assigned_faculty_id": str(prof_vance["_id"]),
                "assigned_faculty_name": prof_vance["name"],
                "attachment_name": "",
                "attachment_path": "",
                "resolution_notes": "Campus Network NOC dispatched a field engineer; replacing the PoE switch on rack 2.",
                "created_at": now - timedelta(days=2),
                "updated_at": now - timedelta(hours=3),
                "resolved_at": None,
                "closed_at": None
            },
            {
                "issue_id": "ISS-2026-00125",
                "title": "Classroom projector not working in Block B Room 302",
                "category": "Classroom",
                "location": "Academic Block B, Lecture Hall 302",
                "description": "The overhead projector displays a persistent red blinking lamp error and turns off after 60 seconds. Lectures for Data Structures cannot proceed with visual slides.",
                "priority": "HIGH",
                "status": "Resolved",
                "student_id": str(maria["_id"]),
                "student_name": maria["name"],
                "student_email": maria["email"],
                "department": maria["department"],
                "assigned_faculty_id": str(prof_vance["_id"]),
                "assigned_faculty_name": prof_vance["name"],
                "attachment_name": "",
                "attachment_path": "",
                "resolution_notes": "AV technicians replaced the projection lamp module and tested HDMI feed with teaching podium. Tested working at 1080p 60Hz.",
                "created_at": now - timedelta(days=4),
                "updated_at": now - timedelta(days=1),
                "resolved_at": now - timedelta(days=1),
                "closed_at": None
            },
            {
                "issue_id": "ISS-2026-00126",
                "title": "Water leakage in hostel block 4 ground floor",
                "category": "Water",
                "location": "Boys Hostel Block 4, Ground Floor Wing A",
                "description": "Continuous pipe leakage near washroom entrance is causing slippery corridor tiles and minor water pooling.",
                "priority": "HIGH",
                "status": "Assigned",
                "student_id": str(david["_id"]),
                "student_name": david["name"],
                "student_email": david["email"],
                "department": david["department"],
                "assigned_faculty_id": str(dr_bell["_id"]),
                "assigned_faculty_name": dr_bell["name"],
                "attachment_name": "",
                "attachment_path": "",
                "resolution_notes": "",
                "created_at": now - timedelta(days=1),
                "updated_at": now - timedelta(hours=8),
                "resolved_at": None,
                "closed_at": None
            },
            {
                "issue_id": "ISS-2026-00127",
                "title": "Broken electrical socket at Library Reading Table 14",
                "category": "Electricity",
                "location": "Central Library, 1st Floor Quiet Study Zone",
                "description": "The 3-pin socket gives off small sparks when plugging in a laptop charger. Needs electrician inspection.",
                "priority": "MEDIUM",
                "status": "Verified",
                "student_id": str(alex["_id"]),
                "student_name": alex["name"],
                "student_email": alex["email"],
                "department": alex["department"],
                "assigned_faculty_id": None,
                "assigned_faculty_name": None,
                "attachment_name": "",
                "attachment_path": "",
                "resolution_notes": "",
                "created_at": now - timedelta(hours=14),
                "updated_at": now - timedelta(hours=6),
                "resolved_at": None,
                "closed_at": None
            },
            {
                "issue_id": "ISS-2026-00128",
                "title": "Campus shuttle breakdown near East Gate",
                "category": "Transport",
                "location": "East Gate Bus Bay",
                "description": "Shuttle Bus #3 battery died and caused queue delays for morning hostel commuters.",
                "priority": "LOW",
                "status": "Submitted",
                "student_id": str(maria["_id"]),
                "student_name": maria["name"],
                "student_email": maria["email"],
                "department": maria["department"],
                "assigned_faculty_id": None,
                "assigned_faculty_name": None,
                "attachment_name": "",
                "attachment_path": "",
                "resolution_notes": "",
                "created_at": now - timedelta(hours=2),
                "updated_at": now - timedelta(hours=2),
                "resolved_at": None,
                "closed_at": None
            }
        ]

        for iss in issues:
            db.issues.update_one(
                {"issue_id": iss["issue_id"]},
                {"$setOnInsert": iss},
                upsert=True
            )

        # 4. Feedback for resolved issue ISS-2026-00125
        db.feedback.update_one(
            {"issue_id": "ISS-2026-00125"},
            {"$setOnInsert": {
                "issue_id": "ISS-2026-00125",
                "student_id": str(maria["_id"]),
                "student_name": maria["name"],
                "rating": 5,
                "comment": "Super quick turnaround! The projector was replaced before afternoon lectures.",
                "created_at": now - timedelta(hours=18)
            }},
            upsert=True
        )

        # 5. Comments on ISS-2026-00124
        db.comments.update_one(
            {"issue_id": "ISS-2026-00124", "message": {"$regex": "^Network engineer"}},
            {"$setOnInsert": {
                "issue_id": "ISS-2026-00124",
                "user_id": str(prof_vance["_id"]),
                "user_name": prof_vance["name"],
                "user_role": "FACULTY",
                "message": "Network engineer has been dispatched with a replacement switch module. Estimated resolution time is 2:00 PM.",
                "created_at": now - timedelta(hours=5)
            }},
            upsert=True
        )

        # 6. Audit Trails
        db.audit_logs.update_one(
            {"issue_id": "ISS-2026-00124", "action": "Issue Submitted"},
            {"$setOnInsert": {
                "issue_id": "ISS-2026-00124",
                "action": "Issue Submitted",
                "performed_by_id": str(alex["_id"]),
                "performed_by_name": alex["name"],
                "performed_by_role": "STUDENT",
                "details": "Submitted with Priority: CRITICAL",
                "timestamp": now - timedelta(days=2)
            }},
            upsert=True
        )
        db.audit_logs.update_one(
            {"issue_id": "ISS-2026-00124", "action": "Assigned to Faculty"},
            {"$setOnInsert": {
                "issue_id": "ISS-2026-00124",
                "action": "Assigned to Faculty",
                "performed_by_id": str(admin["_id"]),
                "performed_by_name": admin["name"],
                "performed_by_role": "ADMIN",
                "details": f"Assigned to {prof_vance['name']} (CSE)",
                "timestamp": now - timedelta(days=1, hours=12)
            }},
            upsert=True
        )
        db.audit_logs.update_one(
            {"issue_id": "ISS-2026-00124", "action": "Status Changed to In Progress"},
            {"$setOnInsert": {
                "issue_id": "ISS-2026-00124",
                "action": "Status Changed to In Progress",
                "performed_by_id": str(prof_vance["_id"]),
                "performed_by_name": prof_vance["name"],
                "performed_by_role": "FACULTY",
                "details": "Repairs underway with campus NOC.",
                "timestamp": now - timedelta(hours=3)
            }},
            upsert=True
        )

        # 7. Notifications
        db.notifications.update_one(
            {"user_id": str(alex["_id"]), "title": "Issue Submitted Successfully"},
            {"$setOnInsert": {
                "user_id": str(alex["_id"]),
                "title": "Issue Submitted Successfully",
                "message": "Your issue 'Wi-Fi connectivity problem in CSE block' has been registered with ID ISS-2026-00124.",
                "link": "/student/issue/ISS-2026-00124/",
                "is_read": True,
                "type": "success",
                "created_at": now - timedelta(days=2)
            }},
            upsert=True
        )
        db.notifications.update_one(
            {"user_id": str(alex["_id"]), "title": "Issue Status Update: In Progress"},
            {"$setOnInsert": {
                "user_id": str(alex["_id"]),
                "title": "Issue Status Update: In Progress",
                "message": "Your issue ISS-2026-00124 is now 'In Progress'. Field engineers on site.",
                "link": "/student/issue/ISS-2026-00124/",
                "is_read": False,
                "type": "info",
                "created_at": now - timedelta(hours=3)
            }},
            upsert=True
        )

        self.stdout.write(self.style.SUCCESS("[OK] Successfully seeded realistic issues, audit history, and notifications!"))
