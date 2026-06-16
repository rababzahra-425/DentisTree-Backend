"""
In-panel admin notifications (no email).
Respects per-user notification preferences on UserProfile.
"""
from datetime import datetime, timedelta

from .models import AdminNotification, UserProfile

# Maps notification_type -> UserProfile boolean field
PREF_FIELD_MAP = {
    "new_appointment": "notif_new_appointments",
    "appointment_reminder": "notif_reminders",
    "review": "notif_reviews",
    "inventory": "notif_inventory",
    "financial_report": "notif_reports",
    "system_alert": "notif_system_alerts",
    "staff_update": "notif_staff_updates",
    "supplier_invoice": "notif_invoices",
}


def is_notification_enabled(notification_type: str) -> bool:
    """True if at least one admin profile has this notification type enabled."""
    field = PREF_FIELD_MAP.get(notification_type)
    if not field:
        return True
    profiles = list(UserProfile.objects.only(field).limit(50))
    if not profiles:
        return True
    return any(getattr(p, field, True) for p in profiles)


def create_admin_notification(
    notification_type: str,
    title: str,
    message: str = "",
    link_page: str = "",
    *,
    dedupe_hours: int = 0,
    dedupe_key: str = "",
) -> AdminNotification | None:
    """
    Create an in-panel notification if the type is enabled.
    Optional dedupe: skip if same title+type exists within dedupe_hours.
    """
    if not is_notification_enabled(notification_type):
        return None

    if dedupe_hours and dedupe_key:
        since = datetime.utcnow() - timedelta(hours=dedupe_hours)
        existing = AdminNotification.objects(
            notification_type=notification_type,
            title=title,
            created_at__gte=since,
        ).first()
        if existing:
            return None

    notif = AdminNotification(
        notification_type=notification_type,
        title=title,
        message=message,
        link_page=link_page,
        is_read=False,
    )
    notif.save()
    return notif


def notify_new_appointment(patient_name: str, service_name: str, appt_date: str):
    create_admin_notification(
        "new_appointment",
        "New appointment booked",
        f"{patient_name} — {service_name} on {appt_date}",
        link_page="appointments",
    )


def notify_new_review(customer_name: str, rating: int):
    create_admin_notification(
        "review",
        "New patient review",
        f"{customer_name} rated {rating}/5 stars",
        link_page="reviews",
    )


def notify_low_inventory(item_name: str, quantity: float, threshold: float):
    create_admin_notification(
        "inventory",
        "Low inventory alert",
        f"{item_name}: {quantity} left (threshold {threshold})",
        link_page="inventory",
        dedupe_hours=24,
        dedupe_key=item_name,
    )


def notify_staff_update(employee_name: str, action: str = "added"):
    create_admin_notification(
        "staff_update",
        "Staff update",
        f"{employee_name} was {action}",
        link_page="employees",
    )


def notify_system(title: str, message: str):
    create_admin_notification(
        "system_alert",
        title,
        message,
        link_page="settings",
    )
