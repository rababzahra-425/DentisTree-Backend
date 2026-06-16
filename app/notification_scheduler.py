"""
Scheduled in-panel notifications (no email).
Triggered on notification poll/feed — throttled via NotificationSchedulerState.
"""
import calendar
import datetime

import pytz

from .models import Appointment, Payment, Expense, Employee, InventoryItem, NotificationSchedulerState
from .notification_utils import create_admin_notification, PREF_FIELD_MAP

TZ = pytz.timezone("Asia/Karachi")
REMINDER_JOB = "appointment_reminders"
MONTHLY_JOB = "month_end_financial"
SALARY_RESET_JOB = "monthly_salary_reset"
REMINDER_INTERVAL = datetime.timedelta(minutes=5)
MONTHLY_INTERVAL = datetime.timedelta(hours=6)
SALARY_RESET_INTERVAL = datetime.timedelta(hours=6)  # re-check every 6h so we don't miss midnight


def _should_run(job_key: str, interval: datetime.timedelta) -> bool:
    now = datetime.datetime.utcnow()
    doc = NotificationSchedulerState.objects(job_key=job_key).first()
    if doc and doc.last_run_at and (now - doc.last_run_at) < interval:
        return False
    if not doc:
        doc = NotificationSchedulerState(job_key=job_key)
    doc.last_run_at = now
    doc.save()
    return True


def _normalize_dt(dt):
    if not dt:
        return None
    if dt.tzinfo is None:
        return TZ.localize(dt)
    return dt.astimezone(TZ)


def _month_totals(year: int, month: int):
    _, last_day = calendar.monthrange(year, month)
    month_start = TZ.localize(datetime.datetime(year, month, 1, 0, 0, 0))
    month_end = TZ.localize(datetime.datetime(year, month, last_day, 23, 59, 59))
    month_key = f"{year}-{str(month).zfill(2)}"

    revenue = sum(
        float(p.amount or 0)
        for p in Payment.objects(
            status="Paid",
            created_at__gte=month_start,
            created_at__lte=month_end,
        ).only("amount")
    )

    salary_total = sum(
        float(e.salary or 0) for e in Employee.objects(status="Active").only("salary")
    )
    inventory_total = sum(
        float(i.cost_price or 0) * float(i.quantity or 0)
        for i in InventoryItem.objects.only("cost_price", "quantity")
    )
    manual_expenses = sum(
        float(e.amount or 0)
        for e in Expense.objects(month=month_key).only("amount")
    )
    expenses = salary_total + inventory_total + manual_expenses
    net = revenue - expenses
    return revenue, expenses, net, month_start.strftime("%B %Y")


def _process_month_end_financial():
    now = datetime.datetime.now(TZ)
    year, month = now.year, now.month
    _, last_day = calendar.monthrange(year, month)

    # Fire on the last calendar day of the month (any time that day)
    if now.day != last_day:
        return

    if not _should_run(MONTHLY_JOB, MONTHLY_INTERVAL):
        return

    revenue, expenses, net, label = _month_totals(year, month)
    create_admin_notification(
        "financial_report",
        f"Monthly financial summary — {label}",
        (
            f"Revenue: Rs. {revenue:,.0f} · Expenses: Rs. {expenses:,.0f} · "
            f"Net: Rs. {net:,.0f}. View the full report in Financial Report."
        ),
        link_page="financial-report",
        dedupe_hours=24 * 35,
        dedupe_key=f"monthly-{year}-{month:02d}",
    )


def _process_appointment_reminders():
    if not _should_run(REMINDER_JOB, REMINDER_INTERVAL):
        return

    now = datetime.datetime.now(TZ)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + datetime.timedelta(days=1)
    window_start = now + datetime.timedelta(minutes=50)
    window_end = now + datetime.timedelta(minutes=70)

    candidates = Appointment.objects(
        date__gte=today_start,
        date__lt=today_end,
        status__in=["Pending", "Approved", "Delay"],
    ).only(
        "patient_name",
        "service_name",
        "date",
        "appointment_serial",
    )

    for appt in candidates:
        appt_dt = _normalize_dt(appt.date)
        if not appt_dt:
            continue
        if not (window_start <= appt_dt <= window_end):
            continue

        service = (appt.service_name or "appointment").strip()
        time_str = appt_dt.strftime("%I:%M %p")
        serial = appt.appointment_serial or "—"
        patient = appt.patient_name or "Patient"

        title = f"Reminder: {patient} at {time_str}"
        create_admin_notification(
            "appointment_reminder",
            title,
            (
                f"Today this patient has an appointment in about 1 hour — "
                f"{service} (ID #{serial}). Please ensure the clinic is ready."
            ),
            link_page="appointments",
            dedupe_hours=3,
            dedupe_key=str(appt.id),
        )


def run_scheduled_notifications():
    """Entry point — safe to call on every authenticated poll."""
    try:
        _process_appointment_reminders()
        _process_month_end_financial()
        _process_monthly_salary_reset()
    except Exception:
        import traceback
        traceback.print_exc()


def _process_monthly_salary_reset():
    """
    On the 1st of every month (Asia/Karachi time), reset all employees'
    salary_status to 'Unpaid'. Throttled to run at most once per 6 hours
    so it fires reliably even if the server is busy around midnight.
    """
    now = datetime.datetime.now(TZ)

    # Only act on the 1st day of the month
    if now.day != 1:
        return

    if not _should_run(SALARY_RESET_JOB, SALARY_RESET_INTERVAL):
        return

    try:
        updated = Employee.objects().update(salary_status="Unpaid")
        # Fire an in-panel notification so the admin knows it happened
        create_admin_notification(
            "staff_update",
            "Monthly salary reset",
            f"All {updated} employee salary statuses have been reset to Unpaid for {now.strftime('%B %Y')}.",
            link_page="employees",
            dedupe_hours=24 * 35,
            dedupe_key=f"salary-reset-{now.year}-{now.month:02d}",
        )
    except Exception:
        import traceback
        traceback.print_exc()


def enabled_notification_types_for_feed():
    """Types shown in feed based on user prefs (excludes removed categories)."""
    from .models import UserProfile

    excluded = {"system_alert", "staff_update", "supplier_invoice"}
    enabled = set()
    profiles = list(UserProfile.objects().limit(50))
    if not profiles:
        return {k for k in PREF_FIELD_MAP if k not in excluded}
    for ntype, field in PREF_FIELD_MAP.items():
        if ntype in excluded:
            continue
        if any(getattr(p, field, True) for p in profiles):
            enabled.add(ntype)
    return enabled
