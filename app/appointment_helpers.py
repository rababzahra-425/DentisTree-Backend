"""Fast appointment list serialization (MongoEngine, no broken DBRef crashes)."""
from datetime import datetime

import pytz
from .models import Appointment, Service

APPOINTMENT_LIST_FIELDS = (
    "id",
    "appointment_serial",
    "patient_name",
    "patient_email",
    "patient_phone",
    "service",
    "service_name",
    "date",
    "proposed_date",
    "status",
)

PKT = pytz.timezone("Asia/Karachi")


def display_status(status):
    """Canonical UI/API status. Legacy `Delay` records show as Delayed."""
    raw = (status or "Pending").strip()
    if raw.lower() in ("delay", "delayed"):
        return "Delayed"
    return raw or "Pending"


def _as_pkt(dt):
    if not dt:
        return None
    if getattr(dt, "tzinfo", None) is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(PKT)


def format_proposed_date(dt):
    """Long form for emails, e.g. Monday, 17 November 2026."""
    pkt_dt = _as_pkt(dt)
    if not pkt_dt:
        return ""
    try:
        return pkt_dt.strftime("%A, %d %B %Y")
    except Exception:
        return str(dt)


def _fmt_date_only(dt):
    pkt_dt = _as_pkt(dt)
    if not pkt_dt:
        return ""
    try:
        return pkt_dt.strftime("%d %b %Y")
    except Exception:
        return str(dt)


def parse_proposed_date(raw):
    """
    Parse admin-selected proposed date (YYYY-MM-DD, optionally with time).
    Must be today or later in Asia/Karachi. Does not replace the original slot.
    """
    value = str(raw or "").strip()
    if not value:
        raise ValueError("A proposed appointment date is required.")

    naive = None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            naive = datetime.strptime(value, fmt)
            break
        except ValueError:
            continue
    if naive is None:
        raise ValueError("Proposed date must be in YYYY-MM-DD format.")

    if naive.hour == 0 and naive.minute == 0 and naive.second == 0:
        naive = naive.replace(hour=9, minute=0)
    aware = PKT.localize(naive)
    today = datetime.now(PKT).date()
    if aware.date() < today:
        raise ValueError("Proposed appointment date cannot be in the past.")
    return aware


def _fmt_date(dt):
    """Convert a UTC-stored datetime to PKT and format as 12-hour string."""
    if not dt:
        return "—"
    try:
        # MongoDB stores naive UTC datetimes — make them timezone-aware first
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        pkt_dt = dt.astimezone(PKT)
        return pkt_dt.strftime("%d %b %Y, %I:%M %p")   # e.g. 01 Jun 2026, 06:00 PM
    except Exception:
        return str(dt)


def service_id_from_ref(ref):
    if ref is None:
        return None
    return ref.id if hasattr(ref, "id") else ref


def build_service_map(appointments):
    service_ids = []
    for appt in appointments:
        sid = service_id_from_ref(appt._data.get("service"))
        if sid is not None:
            service_ids.append(sid)
    if not service_ids:
        return {}
    return {
        str(svc.id): svc.name
        for svc in Service.objects(id__in=service_ids).only("id", "name")
    }


def serialize_appointment(appt, service_map):
    serial_val = appt.appointment_serial if appt.appointment_serial is not None else 0
    cached_name = getattr(appt, "service_name", None) or ""
    sid = service_id_from_ref(appt._data.get("service"))
    if cached_name:
        service_name = cached_name
    elif sid:
        service_name = service_map.get(str(sid), "Service Deleted")
    else:
        service_name = "—"
    return {
        "id": str(appt.id),
        "appointment_serial": serial_val,
        "patient_serial": serial_val,
        "patient_name": appt.patient_name or "Unknown Patient",
        "patient_email": appt.patient_email or "",
        "patient_phone": appt.patient_phone or "",
        "service": service_name,
        "date": _fmt_date(appt.date),
        "proposed_date": _fmt_date_only(getattr(appt, "proposed_date", None)),
        "status": display_status(appt.status),
    }


def sort_appointment_rows(rows):
    pending = [r for r in rows if r["status"] == "Pending"]
    pending.sort(key=lambda x: x["id"], reverse=True)
    other = [r for r in rows if r["status"] != "Pending"]
    other.sort(key=lambda x: (-(x["appointment_serial"] or 0), x["id"]))
    return pending + other


def fetch_appointments_list(limit=500):
    """
    Two indexed queries instead of one full scan + Python split.
    Only loads fields needed for the admin list.
    """
    limit = min(max(int(limit), 1), 1000)

    pending_docs = list(
        Appointment.objects.no_dereference()
        .only(*APPOINTMENT_LIST_FIELDS)
        .filter(status="Pending")
        .order_by("-id")[:limit]
    )
    remaining = max(limit - len(pending_docs), 0)
    other_docs = []
    if remaining > 0:
        other_docs = list(
            Appointment.objects.no_dereference()
            .only(*APPOINTMENT_LIST_FIELDS)
            .filter(status__ne="Pending")
            .order_by("-appointment_serial", "-id")[:remaining]
        )

    seen = set()
    all_docs = []
    for doc in pending_docs + other_docs:
        key = str(doc.id)
        if key in seen:
            continue
        seen.add(key)
        all_docs.append(doc)
    service_map = build_service_map(all_docs)
    rows = [serialize_appointment(a, service_map) for a in all_docs]
    return sort_appointment_rows(rows)


def appointments_poll_token():
    """Cheap check for new bookings (used by admin auto-refresh)."""
    latest = Appointment.objects.only("id").order_by("-id").first()
    pending_count = Appointment.objects(status="Pending").count()
    return {
        "latest_id": str(latest.id) if latest else "",
        "pending_count": pending_count,
        "version": f"{latest.id}:{pending_count}" if latest else f"0:{pending_count}",
    }
