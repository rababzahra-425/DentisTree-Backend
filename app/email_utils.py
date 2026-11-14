"""
Appointment email notifications.

Sends:
  - admin alert when a patient books from the website
  - patient confirmation / rejection / delay emails after a status update

SMTP credentials stay in environment variables. Failures are logged
(without passwords) and never raised to the booking/status API unless
the caller chooses to.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection

logger = logging.getLogger("app.email")

CLINIC_NAME = "DentisTree Dental Clinic"
CLINIC_PHONE = "+92 321 7450249"
CLINIC_ADDRESS = "Main Market, Farid Town, Sahiwal, Punjab, Pakistan"

_STATUS_ALIASES = {
    "approved": "Approved",
    "accepted": "Approved",
    "confirm": "Approved",
    "confirmed": "Approved",
    "cancelled": "Cancelled",
    "canceled": "Cancelled",
    "rejected": "Cancelled",
    "reject": "Cancelled",
    "delay": "Delayed",
    "delayed": "Delayed",
    "reschedule": "Delayed",
}


def _redact_email(addr: str | None) -> str:
    if not addr or "@" not in str(addr):
        return "(none)"
    local, domain = str(addr).split("@", 1)
    prefix = local[:1] if local else "?"
    return f"{prefix}***@{domain}"


def normalize_status(status: str | None) -> str | None:
    if not status:
        return None
    key = str(status).strip().lower()
    return _STATUS_ALIASES.get(key, str(status).strip())


def email_is_configured() -> bool:
    user = (getattr(settings, "EMAIL_HOST_USER", None) or "").strip()
    password = (getattr(settings, "EMAIL_HOST_PASSWORD", None) or "").strip()
    return bool(user and password)


def get_from_email() -> str:
    configured = (getattr(settings, "DEFAULT_FROM_EMAIL", None) or "").strip()
    host_user = (getattr(settings, "EMAIL_HOST_USER", None) or "").strip()
    if configured:
        return configured
    if host_user:
        return f"{CLINIC_NAME} <{host_user}>"
    return CLINIC_NAME


def get_admin_email() -> str | None:
    admin = (getattr(settings, "ADMIN_EMAIL", None) or "").strip()
    if admin:
        return admin
    host_user = (getattr(settings, "EMAIL_HOST_USER", None) or "").strip()
    return host_user or None


def _smtp_log_context() -> str:
    """Host/user only — never include the password."""
    return (
        f"host={getattr(settings, 'EMAIL_HOST', '')} "
        f"port={getattr(settings, 'EMAIL_PORT', '')} "
        f"tls={getattr(settings, 'EMAIL_USE_TLS', False)} "
        f"ssl={getattr(settings, 'EMAIL_USE_SSL', False)} "
        f"user={_redact_email(getattr(settings, 'EMAIL_HOST_USER', None))}"
    )


def _admin_delivery_address(admin_email: str) -> str:
    """
    Gmail often hides messages whose From and To are the exact same address
    (they sit in Sent and never appear as a new Inbox item). A plus-alias
    still delivers to the same mailbox and shows up as a new message.
    """
    host_user = (getattr(settings, "EMAIL_HOST_USER", None) or "").strip().lower()
    if admin_email.lower() != host_user:
        return admin_email
    if "@" not in admin_email:
        return admin_email
    local, domain = admin_email.split("@", 1)
    if "+" in local:
        return admin_email
    if domain.lower() in ("gmail.com", "googlemail.com"):
        return f"{local}+booking@{domain}"
    return admin_email


def get_admin_recipients(admin_email: str | None = None) -> list[str]:
    """Clinic inbox first, plus Gmail alias when From and To would otherwise match."""
    admin_email = (admin_email or get_admin_email() or "").strip()
    if not admin_email:
        return []
    recipients = [admin_email]
    alias = _admin_delivery_address(admin_email)
    if alias.lower() not in {addr.lower() for addr in recipients}:
        recipients.append(alias)
    return recipients


def format_proposed_date(dt) -> str:
    if not dt:
        return ""
    try:
        import pytz

        pkt = pytz.timezone("Asia/Karachi")
        if getattr(dt, "tzinfo", None) is None:
            dt = pytz.utc.localize(dt)
        return dt.astimezone(pkt).strftime("%A, %d %B %Y")
    except Exception:
        return str(dt)


def format_appointment_datetime(appointment) -> str:
    try:
        import pytz

        pkt = pytz.timezone("Asia/Karachi")
        dt = appointment.date
        if dt is None:
            return "Not specified"
        if getattr(dt, "tzinfo", None) is None:
            dt = pytz.utc.localize(dt)
        return dt.astimezone(pkt).strftime("%A, %d %B %Y at %I:%M %p")
    except Exception:
        return str(getattr(appointment, "date", None) or "Not specified")


def _smtp_connection_kwargs_list() -> list[dict[str, Any]]:
    """Primary SMTP settings, then Gmail implicit-SSL on 465 if STARTTLS/587 is dropped."""
    timeout = getattr(settings, "EMAIL_TIMEOUT", 12)
    user = getattr(settings, "EMAIL_HOST_USER", None)
    password = getattr(settings, "EMAIL_HOST_PASSWORD", None)
    host = getattr(settings, "EMAIL_HOST", "smtp.gmail.com") or "smtp.gmail.com"
    primary = {
        "host": host,
        "port": int(getattr(settings, "EMAIL_PORT", 587) or 587),
        "username": user,
        "password": password,
        "use_tls": bool(getattr(settings, "EMAIL_USE_TLS", True)),
        "use_ssl": bool(getattr(settings, "EMAIL_USE_SSL", False)),
        "timeout": timeout,
    }
    attempts = [primary]
    if str(host).lower() == "smtp.gmail.com" and int(primary["port"]) != 465:
        attempts.append(
            {
                "host": host,
                "port": 465,
                "username": user,
                "password": password,
                "use_tls": False,
                "use_ssl": True,
                "timeout": timeout,
            }
        )
    return attempts


def _send_email_with_retry(msg: EmailMultiAlternatives, max_retries: int = 2) -> None:
    last_err = None
    for kwargs in _smtp_connection_kwargs_list():
        for attempt in range(max_retries):
            connection = get_connection(fail_silently=False, **kwargs)
            try:
                connection.open()
                msg.connection = connection
                connection.send_messages([msg])
                return
            except Exception as err:
                last_err = err
                logger.warning(
                    "Email send attempt %s/%s failed (host=%s port=%s tls=%s ssl=%s user=%s): %s",
                    attempt + 1,
                    max_retries,
                    kwargs.get("host"),
                    kwargs.get("port"),
                    kwargs.get("use_tls"),
                    kwargs.get("use_ssl"),
                    _redact_email(kwargs.get("username")),
                    err,
                )
                if attempt < max_retries - 1:
                    time.sleep(1)
            finally:
                try:
                    connection.close()
                except Exception:
                    pass
                msg.connection = None
    raise last_err


def send_message(msg: EmailMultiAlternatives) -> bool:
    recipients = ", ".join(_redact_email(a) for a in (msg.to or []))
    if not email_is_configured():
        logger.error(
            "Email skipped: EMAIL_HOST_USER or EMAIL_HOST_PASSWORD is not set. "
            "to=%s subject=%r %s",
            recipients,
            msg.subject,
            _smtp_log_context(),
        )
        return False
    try:
        _send_email_with_retry(msg)
        logger.info(
            "Email sent to %s subject=%r %s",
            recipients,
            msg.subject,
            _smtp_log_context(),
        )
        return True
    except Exception:
        logger.exception(
            "Email delivery failed to %s subject=%r %s",
            recipients,
            msg.subject,
            _smtp_log_context(),
        )
        return False


def resolve_patient_email(appointment) -> str | None:
    candidates = [
        getattr(appointment, "patient_email", None),
        getattr(getattr(appointment, "patient", None), "email", None),
    ]
    for value in candidates:
        email = (value or "").strip()
        if email:
            return email
    return None


def send_admin_booking_email(appointment) -> bool:
    """Notify the clinic admin that a new appointment was booked."""
    admin_email = get_admin_email()
    if not admin_email:
        logger.error("Admin booking email skipped: ADMIN_EMAIL / EMAIL_HOST_USER not configured")
        return False

    patient_name = getattr(appointment, "patient_name", None) or "Unknown Patient"
    patient_email = getattr(appointment, "patient_email", None) or "Not provided"
    patient_phone = getattr(appointment, "patient_phone", None) or "Not provided"
    service_name = getattr(appointment, "service_name", None) or "Dental Consultation"
    date_str = format_appointment_datetime(appointment)
    recipients = get_admin_recipients(admin_email)

    subject = f"New Appointment Booking — {CLINIC_NAME}"
    plain = (
        f"New appointment booked!\n\n"
        f"Patient Name : {patient_name}\n"
        f"Email        : {patient_email}\n"
        f"Phone        : {patient_phone}\n"
        f"Service      : {service_name}\n"
        f"Date & Time  : {date_str}\n\n"
        f"Please review this appointment in the admin panel."
    )
    html = _admin_booking_html(
        patient_name, patient_email, patient_phone, service_name, date_str
    )

    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain,
        from_email=get_from_email(),
        to=recipients,
        reply_to=[admin_email],
    )
    msg.attach_alternative(html, "text/html")
    logger.info(
        "Sending admin booking email for patient=%s to=%s",
        _redact_email(patient_email if "@" in str(patient_email) else None),
        ", ".join(_redact_email(a) for a in recipients),
    )
    return send_message(msg)


def patient_email_failure_reason(appointment) -> str:
    """Human-readable reason after a status email failed to send."""
    if not resolve_patient_email(appointment):
        return "The booking has no patient email address."
    if not email_is_configured():
        return (
            "SMTP is not configured. Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD "
            "on the server and restart it."
        )
    return (
        "Gmail rejected the SMTP username/password. Create a new 16-character "
        "App Password at https://myaccount.google.com/apppasswords, set "
        "EMAIL_HOST_PASSWORD, and restart the server."
    )


def send_appointment_status_email(appointment, status: str, extra: dict[str, Any] | None = None) -> bool:
    """Notify the patient after Approved / Cancelled / Delayed."""
    extra = extra or {}
    status = normalize_status(status)
    patient_email = resolve_patient_email(appointment)
    if not patient_email:
        logger.error(
            "Patient status email skipped: appointment has no patient email (status=%s)",
            status,
        )
        return False
    if status not in ("Approved", "Cancelled", "Delayed"):
        logger.warning("Patient status email skipped: unknown status %r", status)
        return False

    patient_name = getattr(appointment, "patient_name", None) or "Valued Patient"
    service_name = getattr(appointment, "service_name", None) or "Dental Consultation"
    date_str = extra.get("date_str") or format_appointment_datetime(appointment)
    proposed_date_str = (
        extra.get("proposed_date_str")
        or format_proposed_date(getattr(appointment, "proposed_date", None))
        or date_str
    )

    subject, plain, html = _patient_status_content(
        status, patient_name, service_name, date_str, proposed_date_str
    )

    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain,
        from_email=get_from_email(),
        to=[patient_email],
        reply_to=[get_admin_email() or get_from_email()],
    )
    msg.attach_alternative(html, "text/html")
    return send_message(msg)


# Keep the historical names used by views.py
_send_admin_booking_email = send_admin_booking_email
_send_appointment_email = send_appointment_status_email
_send_email_with_retry_public = _send_email_with_retry


def _admin_booking_html(patient_name, patient_email, patient_phone, service_name, date_str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/></head>
<body style="margin:0;padding:0;background:#f0f4f8;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4f8;padding:40px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:16px;overflow:hidden;
                    box-shadow:0 4px 24px rgba(0,0,0,0.10);max-width:600px;width:100%;">
        <tr>
          <td style="background:linear-gradient(135deg,#1d4ed8 0%,#0d9488 100%);
                     padding:36px 40px;text-align:center;">
            <div style="font-size:40px;margin-bottom:10px;">&#128197;</div>
            <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;
                       letter-spacing:-0.3px;">{CLINIC_NAME}</h1>
            <p style="margin:6px 0 0;color:rgba(255,255,255,0.80);font-size:13px;">
              New Appointment Booking
            </p>
          </td>
        </tr>
        <tr>
          <td align="center" style="padding:28px 40px 0;">
            <span style="display:inline-block;background:#1d4ed81a;color:#1d4ed8;
                         border:1.5px solid #1d4ed840;border-radius:30px;
                         padding:7px 22px;font-size:13px;font-weight:700;
                         letter-spacing:0.05em;">NEW BOOKING</span>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 40px 32px;">
            <p style="margin:0 0 18px;font-size:15px;color:#1e293b;">
              A new appointment has been booked by a patient.
            </p>
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="background:#f8fafc;border:1px solid #e2e8f0;
                          border-radius:12px;margin:24px 0;overflow:hidden;">
              <tr>
                <td style="padding:14px 20px;border-bottom:1px solid #e2e8f0;">
                  <span style="font-size:11px;font-weight:700;color:#94a3b8;
                               text-transform:uppercase;letter-spacing:0.06em;">
                    Patient Name
                  </span><br/>
                  <span style="font-size:14px;font-weight:600;color:#0f172a;">
                    {patient_name}
                  </span>
                </td>
              </tr>
              <tr>
                <td style="padding:14px 20px;border-bottom:1px solid #e2e8f0;">
                  <span style="font-size:11px;font-weight:700;color:#94a3b8;
                               text-transform:uppercase;letter-spacing:0.06em;">
                    Email
                  </span><br/>
                  <span style="font-size:14px;font-weight:600;color:#0f172a;">
                    {patient_email}
                  </span>
                </td>
              </tr>
              <tr>
                <td style="padding:14px 20px;border-bottom:1px solid #e2e8f0;">
                  <span style="font-size:11px;font-weight:700;color:#94a3b8;
                               text-transform:uppercase;letter-spacing:0.06em;">
                    Phone
                  </span><br/>
                  <span style="font-size:14px;font-weight:600;color:#0f172a;">
                    {patient_phone}
                  </span>
                </td>
              </tr>
              <tr>
                <td style="padding:14px 20px;border-bottom:1px solid #e2e8f0;">
                  <span style="font-size:11px;font-weight:700;color:#94a3b8;
                               text-transform:uppercase;letter-spacing:0.06em;">
                    Service
                  </span><br/>
                  <span style="font-size:14px;font-weight:600;color:#0f172a;">
                    {service_name}
                  </span>
                </td>
              </tr>
              <tr>
                <td style="padding:14px 20px;">
                  <span style="font-size:11px;font-weight:700;color:#94a3b8;
                               text-transform:uppercase;letter-spacing:0.06em;">
                    Date &amp; Time
                  </span><br/>
                  <span style="font-size:14px;font-weight:600;color:#0f172a;">
                    {date_str}
                  </span>
                </td>
              </tr>
            </table>
            <p style="margin:0;font-size:13.5px;color:#64748b;line-height:1.6;">
              Please review and respond to this appointment in the admin panel.
            </p>
          </td>
        </tr>
        <tr>
          <td style="background:#f8fafc;border-top:1px solid #e2e8f0;
                     padding:20px 40px;text-align:center;">
            <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;">
              {CLINIC_NAME}<br/>
              This is an automated notification for new bookings.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _wrap_patient_html(accent_color, icon, subject_line, body_html, patient_name, service_name, date_str) -> str:
    clinic_mail = get_admin_email() or "dentistreeclinic123@gmail.com"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{subject_line}</title>
</head>
<body style="margin:0;padding:0;background:#f0f4f8;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4f8;padding:40px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:16px;overflow:hidden;
                    box-shadow:0 4px 24px rgba(0,0,0,0.10);max-width:600px;width:100%;">
        <tr>
          <td style="background:linear-gradient(135deg,#1d4ed8 0%,#0d9488 100%);
                     padding:36px 40px;text-align:center;">
            <div style="font-size:40px;margin-bottom:10px;">{icon}</div>
            <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;
                       letter-spacing:-0.3px;">{CLINIC_NAME}</h1>
            <p style="margin:6px 0 0;color:rgba(255,255,255,0.80);font-size:13px;">
              Your Smile, Our Priority
            </p>
          </td>
        </tr>
        <tr>
          <td align="center" style="padding:28px 40px 0;">
            <span style="display:inline-block;background:{accent_color}1a;
                         color:{accent_color};border:1.5px solid {accent_color}40;
                         border-radius:30px;padding:7px 22px;
                         font-size:13px;font-weight:700;letter-spacing:0.05em;">
              {subject_line.upper()}
            </span>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 40px 32px;">
            <p style="margin:0 0 18px;font-size:15px;color:#1e293b;">
              Dear <strong>{patient_name}</strong>,
            </p>
            {body_html}
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="background:#f8fafc;border:1px solid #e2e8f0;
                          border-radius:12px;margin:24px 0;overflow:hidden;">
              <tr>
                <td style="padding:16px 20px;border-bottom:1px solid #e2e8f0;">
                  <span style="font-size:11px;font-weight:700;color:#94a3b8;
                               text-transform:uppercase;letter-spacing:0.06em;">
                    Service
                  </span><br/>
                  <span style="font-size:14px;font-weight:600;color:#0f172a;">
                    {service_name}
                  </span>
                </td>
              </tr>
              <tr>
                <td style="padding:16px 20px;">
                  <span style="font-size:11px;font-weight:700;color:#94a3b8;
                               text-transform:uppercase;letter-spacing:0.06em;">
                    Date &amp; Time
                  </span><br/>
                  <span style="font-size:14px;font-weight:600;color:#0f172a;">
                    {date_str}
                  </span>
                </td>
              </tr>
            </table>
            <p style="margin:0;font-size:13.5px;color:#64748b;line-height:1.6;">
              If you have any questions, please don't hesitate to contact us at
              <a href="tel:{CLINIC_PHONE.replace(' ', '')}" style="color:#0d9488;text-decoration:none;">
                {CLINIC_PHONE}
              </a>.
            </p>
          </td>
        </tr>
        <tr>
          <td style="background:#f8fafc;border-top:1px solid #e2e8f0;
                     padding:20px 40px;text-align:center;">
            <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;">
              {CLINIC_ADDRESS}<br/>
              <a href="mailto:{clinic_mail}"
                 style="color:#0d9488;text-decoration:none;">{clinic_mail}</a>
            </p>
            <p style="margin:10px 0 0;font-size:11px;color:#cbd5e1;">
              This is an automated message. Please do not reply directly to this email.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _patient_status_content(status, patient_name, service_name, date_str, proposed_date_str=""):
    if status == "Approved":
        subject = f"Appointment Confirmed — {CLINIC_NAME}"
        plain = (
            f"Dear {patient_name},\n\n"
            f"We are pleased to confirm that your appointment has been successfully booked.\n\n"
            f"Service : {service_name}\n"
            f"Date & Time : {date_str}\n\n"
            f"Please arrive 10 minutes before your scheduled time. "
            f"If you need to reschedule, contact us at {CLINIC_PHONE}.\n\n"
            f"Warm regards,\n{CLINIC_NAME}"
        )
        body_html = f"""
            <p style="font-size:15px;color:#1e293b;line-height:1.7;margin:0 0 14px;">
              We are delighted to confirm that your appointment has been
              <strong style="color:#0d9488;">successfully booked</strong>.
              Our team is looking forward to welcoming you.
            </p>
            <p style="font-size:15px;color:#1e293b;line-height:1.7;margin:0 0 14px;">
              As a gentle reminder, please arrive at the clinic
              <strong>at least 10 minutes before</strong> your scheduled time
              so we can ensure a smooth and timely experience for you.
            </p>
            <p style="font-size:15px;color:#1e293b;line-height:1.7;margin:0;">
              Should you need to reschedule or have any questions, please contact us
              as early as possible so we can accommodate you.
            </p>"""
        html = _wrap_patient_html("#0d9488", "✅", "Appointment Confirmed", body_html, patient_name, service_name, date_str)

    elif status == "Cancelled":
        subject = f"Appointment Update — {CLINIC_NAME}"
        plain = (
            f"Dear {patient_name},\n\n"
            f"We regret to inform you that your appointment for {service_name} "
            f"on {date_str} could not be approved at this time due to scheduling "
            f"constraints beyond our control.\n\n"
            f"We sincerely apologise for any inconvenience caused and encourage you "
            f"to book a new appointment at your earliest convenience.\n\n"
            f"Warm regards,\n{CLINIC_NAME}"
        )
        body_html = f"""
            <p style="font-size:15px;color:#1e293b;line-height:1.7;margin:0 0 14px;">
              We regret to inform you that your appointment could
              <strong style="color:#dc2626;">not be approved</strong> at this time.
            </p>
            <p style="font-size:15px;color:#1e293b;line-height:1.7;margin:0 0 14px;">
              Due to unavoidable scheduling conflicts and prior commitments, we are
              unable to accommodate your requested time slot. We sincerely apologise
              for any inconvenience this may have caused.
            </p>
            <p style="font-size:15px;color:#1e293b;line-height:1.7;margin:0;">
              We warmly encourage you to book a new appointment at your earliest
              convenience. Our team will do everything possible to find a suitable
              time that works for you.
            </p>"""
        html = _wrap_patient_html("#dc2626", "❌", "Appointment Not Approved", body_html, patient_name, service_name, date_str)

    else:  # Delayed
        proposed = proposed_date_str or date_str
        subject = "Appointment Rescheduling Update – DentisTree Clinic"
        plain = (
            f"Dear {patient_name},\n\n"
            f"We would like to inform you that your appointment at DentisTree Clinic "
            f"needs to be rescheduled.\n\n"
            f"Proposed New Appointment Date: {proposed}\n\n"
            f"We may be able to accommodate your appointment on the date mentioned above.\n\n"
            f"However, please note that this date is not yet confirmed.\n\n"
            f"Our team will contact you by phone to confirm your availability and "
            f"finalize your appointment details.\n\n"
            f"Thank you for your patience and understanding.\n\n"
            f"Warm regards,\nDentisTree Clinic Team"
        )
        html = _delay_email_html(patient_name, proposed, service_name)

    return subject, plain, html


def _delay_email_html(patient_name, proposed_date_str, service_name) -> str:
    clinic_mail = get_admin_email() or "dentistreeclinic123@gmail.com"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Appointment Rescheduling Update</title>
</head>
<body style="margin:0;padding:0;background:#eef6f8;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#eef6f8;padding:24px 0;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:16px;overflow:hidden;max-width:600px;width:100%;">
        <tr>
          <td style="background:#0f766e;padding:28px 32px;text-align:center;">
            <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;">DentisTree Clinic</h1>
            <p style="margin:8px 0 0;color:#ccfbf1;font-size:13px;">Appointment Rescheduling Update</p>
          </td>
        </tr>
        <tr>
          <td style="padding:28px 32px 8px;">
            <p style="margin:0 0 16px;font-size:16px;color:#0f172a;">Dear {patient_name},</p>
            <p style="margin:0 0 16px;font-size:15px;color:#334155;line-height:1.7;">
              We would like to inform you that your appointment at DentisTree Clinic
              needs to be rescheduled.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:0 32px 8px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
                   style="background:#fffbeb;border:1px solid #fde68a;border-radius:12px;">
              <tr>
                <td style="padding:16px 20px;">
                  <p style="margin:0 0 6px;font-size:11px;font-weight:700;color:#92400e;letter-spacing:0.06em;text-transform:uppercase;">
                    Proposed New Appointment Date
                  </p>
                  <p style="margin:0;font-size:18px;font-weight:700;color:#b45309;">{proposed_date_str}</p>
                  <p style="margin:8px 0 0;font-size:13px;color:#78350f;">Service: {service_name}</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:20px 32px 8px;">
            <p style="margin:0 0 14px;font-size:15px;color:#334155;line-height:1.7;">
              We may be able to accommodate your appointment on the date mentioned above.
            </p>
            <p style="margin:0 0 14px;font-size:15px;color:#334155;line-height:1.7;">
              However, please note that this date is <strong>not yet confirmed</strong>.
            </p>
            <p style="margin:0;font-size:15px;color:#334155;line-height:1.7;">
              Our team will contact you by phone to confirm your availability and
              finalize your appointment details.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:20px 32px 28px;">
            <p style="margin:0 0 16px;font-size:15px;color:#334155;line-height:1.7;">
              Thank you for your patience and understanding.
            </p>
            <p style="margin:0;font-size:15px;color:#0f172a;line-height:1.7;">
              Warm regards,<br/>
              <strong>DentisTree Clinic Team</strong>
            </p>
          </td>
        </tr>
        <tr>
          <td style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:18px 32px;text-align:center;">
            <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;">
              {CLINIC_ADDRESS}<br/>
              {CLINIC_PHONE}<br/>
              <a href="mailto:{clinic_mail}" style="color:#0d9488;text-decoration:none;">{clinic_mail}</a>
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
