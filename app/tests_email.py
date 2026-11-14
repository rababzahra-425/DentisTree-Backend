from datetime import datetime
from types import SimpleNamespace

from django.core import mail
from django.test import SimpleTestCase, override_settings

from app.email_utils import (
    get_admin_recipients,
    normalize_status,
    patient_email_failure_reason,
    send_admin_booking_email,
    send_appointment_status_email,
    send_message,
)


def _appointment(**kwargs):
    defaults = dict(
        patient_name="Ali Hassan",
        patient_email="patient@example.com",
        patient_phone="03001234567",
        service_name="Teeth Cleaning",
        date=datetime(2026, 4, 3, 14, 30),
        patient=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    EMAIL_HOST_USER="dentistreeclinic123@gmail.com",
    EMAIL_HOST_PASSWORD="dummy-password-not-used",
    DEFAULT_FROM_EMAIL="DentisTree Dental Clinic <dentistreeclinic123@gmail.com>",
    ADMIN_EMAIL="dentistreeclinic123@gmail.com",
)
class AppointmentEmailTests(SimpleTestCase):
    def test_admin_booking_email_goes_to_clinic_inbox(self):
        ok = send_admin_booking_email(_appointment())
        self.assertTrue(ok)
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertIn("New Appointment Booking", sent.subject)
        self.assertEqual(
            sent.to,
            [
                "dentistreeclinic123@gmail.com",
                "dentistreeclinic123+booking@gmail.com",
            ],
        )
        self.assertIn("Ali Hassan", sent.body)
        self.assertIn("patient@example.com", sent.body)
        self.assertIn("03001234567", sent.body)

    def test_approved_email_goes_to_patient(self):
        ok = send_appointment_status_email(_appointment(), "Approved")
        self.assertTrue(ok)
        self.assertEqual(mail.outbox[0].to, ["patient@example.com"])
        self.assertIn("Confirmed", mail.outbox[0].subject)

    def test_rejected_alias_sends_cancellation_email(self):
        ok = send_appointment_status_email(_appointment(), "Rejected")
        self.assertTrue(ok)
        self.assertIn("could not be approved", mail.outbox[0].body.lower())

    def test_delay_email_includes_proposed_date(self):
        ok = send_appointment_status_email(
            _appointment(),
            "Delay",
            extra={"proposed_date_str": "Friday, 20 November 2026"},
        )
        self.assertTrue(ok)
        sent = mail.outbox[0]
        self.assertIn("Rescheduling Update", sent.subject)
        self.assertIn("Friday, 20 November 2026", sent.body)
        self.assertIn("not yet confirmed", sent.body.lower())

    def test_failure_reason_when_patient_email_missing(self):
        reason = patient_email_failure_reason(
            _appointment(patient_email="", patient=None)
        )
        self.assertIn("no patient email", reason.lower())

    def test_missing_patient_email_is_not_silent(self):
        with self.assertLogs("app.email", level="ERROR") as logs:
            ok = send_appointment_status_email(
                _appointment(patient_email="", patient=None),
                "Approved",
            )
        self.assertFalse(ok)
        self.assertEqual(len(mail.outbox), 0)
        self.assertTrue(any("no patient email" in line.lower() for line in logs.output))

    def test_status_aliases(self):
        self.assertEqual(normalize_status("accepted"), "Approved")
        self.assertEqual(normalize_status("rejected"), "Cancelled")
        self.assertEqual(normalize_status("delayed"), "Delayed")
        self.assertEqual(normalize_status("Delay"), "Delayed")

    def test_admin_recipients_include_gmail_plus_alias(self):
        self.assertEqual(
            get_admin_recipients("dentistreeclinic123@gmail.com"),
            [
                "dentistreeclinic123@gmail.com",
                "dentistreeclinic123+booking@gmail.com",
            ],
        )

    @override_settings(EMAIL_HOST_USER="", EMAIL_HOST_PASSWORD="")
    def test_missing_smtp_credentials_are_logged_not_silent(self):
        from django.core.mail import EmailMultiAlternatives

        with self.assertLogs("app.email", level="ERROR") as logs:
            ok = send_message(
                EmailMultiAlternatives(
                    subject="x",
                    body="y",
                    from_email="DentisTree Dental Clinic <dentistreeclinic123@gmail.com>",
                    to=["patient@example.com"],
                )
            )
        self.assertFalse(ok)
        self.assertTrue(any("not set" in line.lower() for line in logs.output))
