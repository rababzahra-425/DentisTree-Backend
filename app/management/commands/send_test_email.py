from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand, CommandError

from app.email_utils import get_admin_email, get_from_email, send_message


class Command(BaseCommand):
    help = "Send a test email so SMTP / Gmail app-password issues are easy to diagnose."

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            dest="to_email",
            default="",
            help="Recipient (defaults to ADMIN_EMAIL / EMAIL_HOST_USER).",
        )

    def handle(self, *args, **options):
        to_email = (options.get("to_email") or get_admin_email() or "").strip()
        if not to_email:
            raise CommandError("No recipient. Pass --to or set ADMIN_EMAIL / EMAIL_HOST_USER.")
        if not (getattr(settings, "EMAIL_HOST_USER", None) and getattr(settings, "EMAIL_HOST_PASSWORD", None)):
            raise CommandError("EMAIL_HOST_USER or EMAIL_HOST_PASSWORD is not set.")

        subject = "DentisTree email test"
        body = (
            "This is a test message from the DentisTree Clinic backend.\n"
            "If you received it, SMTP authentication is working."
        )
        msg = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=get_from_email(),
            to=[to_email],
        )
        ok = send_message(msg)
        if not ok:
            raise CommandError(
                "Send failed. Check server logs (app.email). "
                "Gmail requires a 16-character App Password, not the account login password."
            )
        self.stdout.write(self.style.SUCCESS(f"Test email accepted by SMTP for {to_email}"))
