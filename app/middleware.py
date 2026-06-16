"""
security/middleware.py
───────────────────────
SessionTrackerMiddleware
  - Registers each authenticated Django session in UserSession so
    "log out all devices" can terminate them reliably.
  - Runs once per request (no database hit if session already tracked).
"""

from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone


class SessionTrackerMiddleware(MiddlewareMixin):
    """
    Track authenticated sessions in MongoDB via UserSession model.
    Add to settings.MIDDLEWARE *after* SessionMiddleware and AuthenticationMiddleware:

        MIDDLEWARE = [
            ...
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'security.middleware.SessionTrackerMiddleware',   # ← add here
            ...
        ]
    """

    def process_request(self, request):
        # Only track after session + auth middleware have run
        if not hasattr(request, "user") or not hasattr(request, "session"):
            return

        if not request.user.is_authenticated:
            return

        session_key = request.session.session_key
        if not session_key:
            return

        # Lazy import to avoid AppRegistryNotReady at import time
        from .models import UserSession
        from .utils import get_client_ip, get_user_agent

        # Use update_or_create so we don't create duplicates
        # update_fields on 'create' path is handled by defaults
        try:
            UserSession.objects.update_or_create(
                session_key=session_key,
                defaults={
                    "user_id":      str(request.user.id),
                    "ip_address":   get_client_ip(request),
                    "user_agent":   get_user_agent(request),
                    "last_activity": timezone.now(),
                    "is_active":    True,
                },
            )
        except Exception:
            # Never let middleware failures break the request
            pass
