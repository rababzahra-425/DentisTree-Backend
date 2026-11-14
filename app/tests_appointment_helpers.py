from datetime import datetime, timedelta

from django.test import SimpleTestCase

from app.appointment_helpers import display_status, parse_proposed_date, format_proposed_date


class AppointmentHelperTests(SimpleTestCase):
    def test_display_status_maps_legacy_delay(self):
        self.assertEqual(display_status("Delay"), "Delayed")
        self.assertEqual(display_status("Delayed"), "Delayed")
        self.assertEqual(display_status("Pending"), "Pending")

    def test_parse_proposed_date_rejects_past(self):
        past = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        with self.assertRaises(ValueError):
            parse_proposed_date(past)

    def test_parse_proposed_date_accepts_today_or_future(self):
        future = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        parsed = parse_proposed_date(future)
        self.assertEqual(parsed.strftime("%Y-%m-%d"), future)
        self.assertTrue(format_proposed_date(parsed))

    def test_parse_proposed_date_required(self):
        with self.assertRaises(ValueError):
            parse_proposed_date("")
