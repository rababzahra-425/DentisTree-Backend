# """
# security/utils.py
# ──────────────────
# Reusable helpers for:
#   - Password validation
#   - OTP delivery (SMS via Twilio, Email via Django)
#   - TOTP (Authenticator App) via pyotp
#   - Getting client IP / user-agent
# """

# import re
# import logging
# import pyotp
# import qrcode
# import qrcode.image.svg
# import io
# import base64

# from django.core.mail import send_mail
# from django.conf import settings

# logger = logging.getLogger(__name__)


# # ─────────────────────────────────────────────────────────────────────────────
# #  PASSWORD VALIDATION
# # ─────────────────────────────────────────────────────────────────────────────

# def validate_password_strength(password: str) -> list[str]:
#     """
#     Returns a list of error strings. Empty list = password is valid.
#     Rules: ≥8 chars, 1 uppercase, 1 digit, 1 special char.
#     """
#     errors = []
#     if len(password) < 8:
#         errors.append("Password must be at least 8 characters long.")
#     if not re.search(r"[A-Z]", password):
#         errors.append("Password must contain at least one uppercase letter.")
#     if not re.search(r"[0-9]", password):
#         errors.append("Password must contain at least one number.")
#     if not re.search(r"[^A-Za-z0-9]", password):
#         errors.append("Password must contain at least one special character (e.g. @, #, !).")
#     return errors


# # ─────────────────────────────────────────────────────────────────────────────
# #  CLIENT INFO
# # ─────────────────────────────────────────────────────────────────────────────

# def get_client_ip(request) -> str:
#     x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
#     if x_forwarded:
#         return x_forwarded.split(",")[0].strip()
#     return request.META.get("REMOTE_ADDR", "")


# def get_user_agent(request) -> str:
#     return request.META.get("HTTP_USER_AGENT", "")[:300]


# # ─────────────────────────────────────────────────────────────────────────────
# #  SMS OTP  (Twilio)
# #  Set these in settings.py:
# #    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER
# #  If Twilio is not configured, falls back to logging (dev mode).
# # ─────────────────────────────────────────────────────────────────────────────

# def send_sms_otp(phone_number: str, code: str) -> bool:
#     """
#     Send OTP via SMS. Returns True on success.
#     """
#     message = f"[Dentistree] Your verification code is: {code}. Valid for 10 minutes."

#     sid   = getattr(settings, "TWILIO_ACCOUNT_SID",  None)
#     token = getattr(settings, "TWILIO_AUTH_TOKEN",   None)
#     from_ = getattr(settings, "TWILIO_FROM_NUMBER",  None)

#     if not all([sid, token, from_]):
#         # Dev mode: just log
#         logger.info(f"[DEV] SMS OTP to {phone_number}: {code}")
#         return True  # treat as success in dev

#     try:
#         from twilio.rest import Client
#         client = Client(sid, token)
#         client.messages.create(body=message, from_=from_, to=phone_number)
#         logger.info(f"SMS OTP sent to {phone_number}")
#         return True
#     except Exception as e:
#         logger.error(f"Failed to send SMS OTP to {phone_number}: {e}")
#         return False


# # ─────────────────────────────────────────────────────────────────────────────
# #  EMAIL OTP
# # ─────────────────────────────────────────────────────────────────────────────

# def send_email_otp(email: str, code: str, purpose: str = "login") -> bool:
#     """
#     Send OTP via Django email backend. Returns True on success.
#     """
#     subject = "[Dentistree] Your Verification Code"
#     body = (
#         f"Hello,\n\n"
#         f"Your one-time verification code for {purpose} is:\n\n"
#         f"    {code}\n\n"
#         f"This code expires in 10 minutes. Do not share it with anyone.\n\n"
#         f"— Dentistree Security Team"
#     )

#     from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@dentistree.pk")

#     try:
#         send_mail(subject, body, from_email, [email], fail_silently=False)
#         logger.info(f"Email OTP sent to {email} for purpose={purpose}")
#         return True
#     except Exception as e:
#         logger.error(f"Failed to send email OTP to {email}: {e}")
#         return False


# # ─────────────────────────────────────────────────────────────────────────────
# #  TOTP — Authenticator App (Google Authenticator / Authy)
# # ─────────────────────────────────────────────────────────────────────────────

# def generate_totp_secret() -> str:
#     """Generate a new base32 TOTP secret."""
#     return pyotp.random_base32()


# def get_totp_uri(secret: str, username: str, issuer: str = "Dentistree") -> str:
#     """Return the otpauth URI for QR code generation."""
#     totp = pyotp.TOTP(secret)
#     return totp.provisioning_uri(name=username, issuer_name=issuer)


# def generate_totp_qr_base64(secret: str, username: str) -> str:
#     """
#     Generate a QR code PNG as base64 string.
#     Frontend can render it as <img src="data:image/png;base64,..." />
#     """
#     uri = get_totp_uri(secret, username)
#     qr = qrcode.make(uri)
#     buf = io.BytesIO()
#     qr.save(buf, format="PNG")
#     return base64.b64encode(buf.getvalue()).decode("utf-8")


# def verify_totp_code(secret: str, code: str) -> bool:
#     """
#     Verify a 6-digit TOTP code. Allows 1-window drift (30s grace).
#     """
#     if not secret or not code:
#         return False
#     totp = pyotp.TOTP(secret)
#     return totp.verify(code, valid_window=1)





"""
security/utils.py
──────────────────
Reusable helpers for:
  - Password validation
  - OTP delivery (SMS via Twilio, Email via Django)
  - TOTP (Authenticator App) via pyotp
  - Getting client IP / user-agent
"""

import re
import logging
import pyotp
import qrcode
import io
import base64

from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
#  PASSWORD VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

def validate_password_strength(password: str) -> list[str]:
    """
    Returns a list of error strings. Empty list = password is valid.
    Rules: ≥8 chars, 1 uppercase, 1 digit, 1 special char.
    """
    errors = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[0-9]", password):
        errors.append("Password must contain at least one number.")
    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("Password must contain at least one special character (e.g. @, #, !).")
    return errors


# ─────────────────────────────────────────────────────────────────────────────
#  CLIENT INFO
# ─────────────────────────────────────────────────────────────────────────────

def get_client_ip(request) -> str:
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def get_user_agent(request) -> str:
    return request.META.get("HTTP_USER_AGENT", "")[:300]


# ─────────────────────────────────────────────────────────────────────────────
#  SMS OTP  (Twilio)
# ─────────────────────────────────────────────────────────────────────────────

def send_sms_otp(phone_number: str, code: str) -> bool:
    """
    Send OTP via SMS. Returns True on success.
    """
    message = f"[Dentistree] Your verification code is: {code}. Valid for 10 minutes."

    sid   = getattr(settings, "TWILIO_ACCOUNT_SID",  None)
    token = getattr(settings, "TWILIO_AUTH_TOKEN",   None)
    from_ = getattr(settings, "TWILIO_FROM_NUMBER",  None)

    if not all([sid, token, from_]):
        # Dev mode: just log
        logger.info(f"[DEV] SMS OTP to {phone_number}: {code}")
        return True  # treat as success in dev

    try:
        from twilio.rest import Client
        client = Client(sid, token)
        client.messages.create(body=message, from_=from_, to=phone_number)
        logger.info(f"SMS OTP sent to {phone_number}")
        return True
    except Exception as e:
        logger.error(f"Failed to send SMS OTP to {phone_number}: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
#  EMAIL OTP
# ─────────────────────────────────────────────────────────────────────────────

def send_email_otp(email: str, code: str, purpose: str = "login") -> bool:
    """
    Send OTP via Django email backend. Returns True on success.
    """
    subject = "[Dentistree] Your Verification Code"
    body = (
        f"Hello,\n\n"
        f"Your one-time verification code for {purpose} is:\n\n"
        f"    {code}\n\n"
        f"This code expires in 10 minutes. Do not share it with anyone.\n\n"
        f"— Dentistree Security Team"
    )

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@dentistree.pk")

    try:
        send_mail(subject, body, from_email, [email], fail_silently=False)
        logger.info(f"Email OTP sent to {email} for purpose={purpose}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email OTP to {email}: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
#  TOTP — Authenticator App (Google Authenticator / Authy)
# ─────────────────────────────────────────────────────────────────────────────

def generate_totp_secret() -> str:
    """Generate a new base32 TOTP secret."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, username: str, issuer: str = "Dentistree") -> str:
    """Return the otpauth URI for QR code generation."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name=issuer)


def generate_totp_qr_base64(secret: str, username: str) -> str:
    """
    Generate a QR code PNG as base64 string.
    Frontend can render it as <img src="data:image/png;base64,..." />
    """
    uri = get_totp_uri(secret, username)
    qr = qrcode.make(uri)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def verify_totp_code(secret: str, code: str) -> bool:
    """
    Verify a 6-digit TOTP code. Allows 1-window drift (30s grace).
    """
    if not secret or not code:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)