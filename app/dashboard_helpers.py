"""Optimized dashboard aggregation — fewer round-trips to MongoDB."""
import datetime
from datetime import timedelta

import pytz

from .models import (
    Patient,
    Employee,
    Appointment,
    Payment,
    Review,
    InventoryItem,
    Expense,
)
from .appointment_helpers import service_id_from_ref, build_service_map


def fetch_dashboard_data():
    tz = pytz.timezone("Asia/Karachi")
    today = datetime.datetime.now(tz)
    today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    month_start = tz.localize(datetime.datetime(today.year, today.month, 1))
    if today.month == 12:
        month_end = tz.localize(datetime.datetime(today.year + 1, 1, 1))
    else:
        month_end = tz.localize(datetime.datetime(today.year, today.month + 1, 1))

    total_patients = Patient.objects.count()
    total_employees = Employee.objects(status="Active").count()

    today_appointments = Appointment.objects(
        date__gte=today_start, date__lt=today_end
    ).count()
    pending_appointments = Appointment.objects(status="Pending").count()
    approved_appointments = Appointment.objects(status="Approved").count()
    cancelled_appointments = Appointment.objects(status="Cancelled").count()
    new_appointments = Appointment.objects(
        date__gte=month_start, date__lt=month_end
    ).count()

    month_payments = Payment.objects(
        status="Paid",
        created_at__gte=month_start,
        created_at__lt=month_end,
    ).only("amount")
    total_revenue = sum(float(p.amount or 0) for p in month_payments)

    inventory_docs = InventoryItem.objects.only(
        "name", "quantity", "unit", "low_stock_threshold", "category"
    )
    low_stock_items = []
    low_stock_count = 0
    for i in inventory_docs:
        qty = float(i.quantity or 0)
        threshold = float(i.low_stock_threshold or 10)
        if qty <= threshold:
            low_stock_count += 1
            if len(low_stock_items) < 6:
                low_stock_items.append({
                    "name": i.name,
                    "quantity": i.quantity,
                    "unit": i.unit or "pieces",
                    "threshold": i.low_stock_threshold,
                    "category": i.category,
                })

    review_ratings = [r.rating for r in Review.objects.only("rating")]
    total_reviews = len(review_ratings)
    avg_rating = (
        round(sum(review_ratings) / total_reviews, 1) if total_reviews else 0
    )

    def _fmt_dt(dt):
        if not dt:
            return "—"
        if dt.tzinfo is None:
            dt = tz.localize(dt)
        else:
            dt = dt.astimezone(tz)
        return dt.strftime("%b %d, %Y %H:%M")

    # Recently booked / updated — not farthest-future appointment date
    recent_appt_docs = list(
        Appointment.objects.no_dereference()
        .only(
            "patient_name",
            "service",
            "service_name",
            "date",
            "status",
            "created_at",
            "appointment_serial",
        )
        .order_by("-created_at", "-appointment_serial", "-id")[:8]
    )
    svc_map = build_service_map(recent_appt_docs)
    recent_appointments = []
    for a in recent_appt_docs:
        cached = getattr(a, "service_name", None) or ""
        sid = service_id_from_ref(a._data.get("service"))
        if cached:
            sname = cached
        elif sid:
            sname = svc_map.get(str(sid), "Service Deleted")
        else:
            sname = "—"
        recent_appointments.append({
            "id": str(a.id),
            "patient_name": a.patient_name or "—",
            "service": sname,
            "date": _fmt_dt(a.date),
            "status": a.status or "Pending",
            "appointment_serial": a.appointment_serial,
        })

    recent_reviews = [
        {
            "customer_name": r.customer_name or "Anonymous",
            "rating": r.rating,
            "comment": (r.comment or "")[:100],
            "created_at": r.created_at.strftime("%b %d, %Y") if r.created_at else "",
        }
        for r in Review.objects.only(
            "customer_name", "rating", "comment", "created_at"
        ).order_by("-created_at")[:5]
    ]

    week_start = today_start - timedelta(days=6)
    week_payments = Payment.objects(
        status="Paid",
        created_at__gte=week_start,
        created_at__lt=today_end,
    ).only("amount", "created_at")

    day_buckets = {}
    for d in range(7):
        day = today_start - timedelta(days=6 - d)
        day_buckets[day.date()] = {
            "label": day.strftime("%a"),
            "date": day.strftime("%b %d"),
            "revenue": 0.0,
        }

    for p in week_payments:
        if not p.created_at:
            continue
        created = p.created_at
        if created.tzinfo:
            created = created.astimezone(tz)
        day_key = created.date()
        if day_key in day_buckets:
            day_buckets[day_key]["revenue"] += float(p.amount or 0)

    revenue_chart = [
        {**v, "revenue": round(v["revenue"], 2)}
        for _, v in sorted(day_buckets.items())
    ]

    salary_total = sum(
        float(e.salary or 0) for e in Employee.objects(status="Active").only("salary")
    )
    inventory_total = sum(
        float(i.cost_price or 0) * float(i.quantity or 0)
        for i in InventoryItem.objects.only("cost_price", "quantity")
    )

    months = []
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        s_dt = tz.localize(datetime.datetime(y, m, 1))
        if m == 12:
            e_dt = tz.localize(datetime.datetime(y + 1, 1, 1))
        else:
            e_dt = tz.localize(datetime.datetime(y, m + 1, 1))
        months.append((s_dt, e_dt, s_dt.strftime("%b"), f"{y}-{str(m).zfill(2)}"))

    range_start = months[0][0]
    range_end = months[-1][1]

    range_payments = list(
        Payment.objects(
            status="Paid",
            created_at__gte=range_start,
            created_at__lt=range_end,
        ).only("amount", "created_at")
    )

    range_expenses = list(
        Expense.objects(month__in=[m[3] for m in months]).only("amount", "month")
    )

    expenses_by_month = {}
    for e in range_expenses:
        expenses_by_month[e.month] = expenses_by_month.get(e.month, 0) + float(
            e.amount or 0
        )

    def _in_range(created, start, end):
        if not created:
            return False
        if created.tzinfo is None:
            created = tz.localize(created)
        else:
            created = created.astimezone(tz)
        return start <= created < end

    financial_comparison = []
    for s_dt, e_dt, label, month_key in months:
        m_inc = sum(
            float(p.amount or 0)
            for p in range_payments
            if _in_range(p.created_at, s_dt, e_dt)
        )
        m_man_exp = expenses_by_month.get(month_key, 0)
        financial_comparison.append({
            "name": label,
            "income": round(m_inc, 2),
            "expenses": round(m_man_exp + salary_total + inventory_total, 2),
        })

    return {
        "stats": {
            "total_patients": total_patients,
            "total_employees": total_employees,
            "today_appointments": today_appointments,
            "pending_appointments": pending_appointments,
            "approved_appointments": approved_appointments,
            "cancelled_appointments": cancelled_appointments,
            "new_appointments": new_appointments,
            "total_revenue": round(total_revenue, 2),
            "low_stock_count": low_stock_count,
            "total_reviews": total_reviews,
            "avg_rating": avg_rating,
        },
        "recent_appointments": recent_appointments,
        "recent_reviews": recent_reviews,
        "low_stock_items": low_stock_items,
        "revenue_chart": revenue_chart,
        "financial_comparison": financial_comparison,
    }


def dashboard_poll_token():
    latest_appt = (
        Appointment.objects.only("id", "created_at")
        .order_by("-created_at", "-id")
        .first()
    )
    latest_patient = Patient.objects.only("id").order_by("-id").first()
    pending = Appointment.objects(status="Pending").count()
    return {
        "version": ":".join([
            str(latest_appt.id) if latest_appt else "0",
            str(latest_patient.id) if latest_patient else "0",
            str(pending),
        ]),
        "pending_appointments": pending,
    }
