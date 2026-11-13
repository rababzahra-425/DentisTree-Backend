from django.apps import AppConfig


class AppConfig(AppConfig):
    name = 'app'

    def ready(self):
        """Validate email configuration at startup."""
        import os
        user = os.environ.get("EMAIL_HOST_USER")
        pw   = os.environ.get("EMAIL_HOST_PASSWORD")
        if not user or not pw:
            print("=" * 60)
            print("  EMAIL WARNING: EMAIL_HOST_USER or EMAIL_HOST_PASSWORD")
            print("  is not set in the .env file. Email notifications")
            print("  will NOT work until configured.")
            print("  See: project/.env  Email section")
            print("=" * 60)
        else:
            print(f"Email configured for: {user}")
