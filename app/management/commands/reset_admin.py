"""Reset the admin account's credentials (username + password).

Single source of truth for admin recovery. Run when the admin forgets their
login. It renames/resets the one existing admin in place (Django auth /
SQLite) and syncs the mirrored MongoDB UserProfile.

Usage:
    python manage.py reset_admin --username NEWNAME --password 'NEWPASS'
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Reset the admin's username + password (renames the single admin in place)."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True, help="New admin username")
        parser.add_argument("--password", required=True, help="New admin password")

    def handle(self, *args, **options):
        username = (options["username"] or "").strip()
        password = options["password"] or ""

        if not username:
            raise CommandError("Username cannot be empty.")
        if not password:
            raise CommandError("Password cannot be empty.")

        # ── Find the single existing admin (SQLite = source of truth) ─────────
        admins = User.objects.filter(is_superuser=True).order_by("id")
        if admins.count() > 1:
            self.stdout.write(
                self.style.WARNING(
                    f"Found {admins.count()} superusers; resetting only the oldest "
                    f"(id={admins.first().id})."
                )
            )
        user = admins.first()

        # Make sure the new username doesn't collide with a *different* account.
        clash = User.objects.filter(username=username)
        if user:
            clash = clash.exclude(pk=user.pk)
        if clash.exists():
            raise CommandError(
                f"Username '{username}' is already taken by another account."
            )

        if user is None:
            user = User(username=username, email="admin@dentistree.pk")
            created = True
        else:
            user.username = username
            created = False

        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)  # hashes (PBKDF2) before saving
        user.save()

        # ── Sync the mirrored MongoDB profile (best-effort) ───────────────────
        mongo_status = self._sync_mongo_profile(user)

        action = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} admin '{username}'. {mongo_status}\n"
                f"Sign in with the new username and password."
            )
        )

    def _sync_mongo_profile(self, user):
        """Mirror username/flags into the Mongo UserProfile. Auth never depends
        on this, so failures here are non-fatal."""
        try:
            from app.models import UserProfile
        except Exception as exc:  # MongoEngine not importable
            return f"(Mongo profile not synced: {exc})"

        try:
            try:
                profile = UserProfile.objects.get(user_id=str(user.id))
            except UserProfile.DoesNotExist:
                profile = UserProfile(
                    user_id=str(user.id),
                    full_name=user.get_full_name() or user.username,
                )
            profile.username = user.username
            profile.email = user.email or ""
            profile.is_superuser = user.is_superuser
            profile.is_staff = user.is_staff
            profile.save()
            return "Mongo profile synced."
        except Exception as exc:  # Mongo unreachable, etc.
            return f"(Mongo profile not synced: {exc})"
