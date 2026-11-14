from django.apps import AppConfig


class AppConfig(AppConfig):
    name = 'app'

    def ready(self):
        """Validate email configuration at startup."""
        import logging
        from django.conf import settings

        logger = logging.getLogger("app.email")
        user = getattr(settings, "EMAIL_HOST_USER", None)
        pw = getattr(settings, "EMAIL_HOST_PASSWORD", None)
        if not user or not pw:
            logger.warning(
                "EMAIL_HOST_USER or EMAIL_HOST_PASSWORD is not set. "
                "Appointment email notifications will not be sent until configured."
            )
        else:
            logger.info("Email configured for %s", user)
