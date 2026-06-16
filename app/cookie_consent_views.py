"""Public cookie consent logging (GDPR audit trail)."""
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import CookieConsentLog


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()[:45]
    return (request.META.get("REMOTE_ADDR") or "")[:45]


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def record_cookie_consent(request):
    if request.method == "OPTIONS":
        return JsonResponse({})

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    visitor_id = (data.get("visitor_id") or "").strip()[:64]
    if not visitor_id:
        return JsonResponse({"error": "visitor_id required"}, status=400)

    prefs = data.get("preferences") or {}
    action = (data.get("action") or "save_preferences").strip()
    if action not in ("accept_all", "reject_non_essential", "save_preferences"):
        action = "save_preferences"

    CookieConsentLog(
        visitor_id=visitor_id,
        necessary=True,
        analytics=bool(prefs.get("analytics")),
        functional=bool(prefs.get("functional")),
        marketing=bool(prefs.get("marketing")),
        consent_version=(data.get("consent_version") or "1.0")[:16],
        action=action,
        user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:300],
        ip_address=_client_ip(request),
    ).save()

    return JsonResponse({"ok": True})
