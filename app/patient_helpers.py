"""Optimized patient list queries."""
from .models import Patient, Appointment
from .appointment_helpers import service_id_from_ref, build_service_map, serialize_appointment

PATIENT_LIST_FIELDS = (
    "id",
    "name",
    "email",
    "phone",
    "patient_serial",
)


def _serialize_last_appointment(appt, service_map):
    if not appt:
        return None
    row = serialize_appointment(appt, service_map)
    return {
        "id": row["id"],
        "serial": row["appointment_serial"],
        "service": row["service"],
        "date": row["date"],
        "status": row["status"],
    }


def fetch_patients_list(limit=500):
    """
    Fast patient list: scalar fields only + one batch appointment lookup
    for last service (no per-patient N+1 dereferencing).
    """
    limit = min(max(int(limit), 1), 2000)
    patients = list(
        Patient.objects.no_dereference()
        .only(*PATIENT_LIST_FIELDS)
        .order_by("-patient_serial", "-id")[:limit]
    )

    if not patients:
        return []

    phones = [p.phone for p in patients if p.phone]
    patient_ids = [p.id for p in patients]

    appt_qs = Appointment.objects.no_dereference().only(
        "id",
        "appointment_serial",
        "patient_name",
        "patient_email",
        "patient_phone",
        "service",
        "service_name",
        "date",
        "status",
        "patient",
    )

    # Latest appointments — one pass
    recent_appts = list(appt_qs.order_by("-date")[: max(limit * 3, 200)])

    service_map = build_service_map(recent_appts)

    by_phone = {}
    by_patient_id = {}
    for appt in recent_appts:
        phone = (appt.patient_phone or "").strip()
        if phone and phone not in by_phone:
            by_phone[phone] = appt
        pid = service_id_from_ref(appt._data.get("patient"))
        if pid is not None:
            key = str(pid)
            if key not in by_patient_id:
                by_patient_id[key] = appt

    rows = []
    for p in patients:
        pid = str(p.id)
        phone = (p.phone or "").strip()
        last_appt = by_patient_id.get(pid) or (by_phone.get(phone) if phone else None)
        last = _serialize_last_appointment(last_appt, service_map)

        rows.append({
            "id": pid,
            "patient_serial": p.patient_serial,
            "name": p.name,
            "email": p.email,
            "phone": p.phone or "",
            "appointments": [last] if last else [],
            "payments": [],
        })

    return rows


def patients_poll_token():
    latest = Patient.objects.only("id").order_by("-id").first()
    count = Patient.objects.count()
    return {
        "latest_id": str(latest.id) if latest else "",
        "count": count,
        "version": f"{latest.id}:{count}" if latest else f"0:{count}",
    }
