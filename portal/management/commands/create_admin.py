"""
Django Management Command to Create or Reset an Administrator Account in MongoDB.
Usage:
    python manage.py create_admin
    python manage.py create_admin --email myadmin@campus.edu --password mysecretpass --name "Chief Admin"
"""

import sys
import getpass
from datetime import datetime, timezone
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from portal.db import get_db


class Command(BaseCommand):
    help = "Creates or updates an Administrator account in the MongoDB Atlas database."

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Administrator login email address')
        parser.add_argument('--password', type=str, help='Administrator password')
        parser.add_argument('--name', type=str, help='Administrator full name')

    def handle(self, *args, **options):
        db = get_db()
        email = options.get('email')
        password = options.get('password')
        name = options.get('name')

        # Interactive prompts if not provided via CLI flags
        if not email:
            try:
                email = input("Enter Administrator Email [admin@campus.edu]: ").strip()
            except (KeyboardInterrupt, EOFError):
                self.stdout.write("\nAborted.")
                return
            if not email:
                email = "admin@campus.edu"

        email = email.lower()

        if not name:
            try:
                name = input("Enter Administrator Name [System Administrator]: ").strip()
            except (KeyboardInterrupt, EOFError):
                self.stdout.write("\nAborted.")
                return
            if not name:
                name = "System Administrator"

        if not password:
            while True:
                try:
                    p1 = getpass.getpass("Enter Password (min 6 characters): ")
                    if len(p1) < 6:
                        self.stdout.write(self.style.WARNING("Password must be at least 6 characters long."))
                        continue
                    p2 = getpass.getpass("Confirm Password: ")
                    if p1 != p2:
                        self.stdout.write(self.style.ERROR("Passwords do not match. Please try again."))
                        continue
                    password = p1
                    break
                except (KeyboardInterrupt, EOFError):
                    self.stdout.write("\nAborted.")
                    return

        now = datetime.now(timezone.utc)
        hashed = make_password(password)

        existing = db.users.find_one({"email": email})
        if existing:
            db.users.update_one(
                {"email": email},
                {
                    "$set": {
                        "name": name,
                        "role": "ADMIN",
                        "password_hash": hashed,
                        "is_active": True,
                        "updated_at": now
                    }
                }
            )
            self.stdout.write(self.style.SUCCESS(
                f"\n[OK] Administrator account '{email}' updated successfully!"
            ))
        else:
            db.users.insert_one({
                "name": name,
                "email": email,
                "role": "ADMIN",
                "department": "Campus Operations",
                "password_hash": hashed,
                "is_active": True,
                "created_at": now,
                "updated_at": now
            })
            self.stdout.write(self.style.SUCCESS(
                f"\n[OK] Administrator account '{email}' created successfully in MongoDB!"
            ))

        self.stdout.write(self.style.MIGRATE_HEADING("Login Details:"))
        self.stdout.write(f"  * Role:     ADMINISTRATOR")
        self.stdout.write(f"  * Email:    {email}")
        self.stdout.write(f"  * Password: {'*' * len(password)}")
        self.stdout.write(f"  * URL:      /admin/login/\n")
