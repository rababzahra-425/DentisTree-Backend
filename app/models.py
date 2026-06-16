import os
from mongoengine import connect, Document, StringField, DateTimeField, ReferenceField, FloatField, IntField, EmailField, ListField
import datetime, json
# from datetime import datetime

# Connect to MongoDB Atlas
# Using direct shard hostnames to bypass local DNS resolution issues with +srv URIs.
# If your DNS is fixed, you can revert to the +srv URI:
#   host="mongodb+srv://rababzahra:Rabab%407272@dentalclinic.vgo1spa.mongodb.net/Dentistree_Dental_Clinic?retryWrites=true&w=majority"
connect(
    db=os.environ.get("MONGO_DB_NAME"),
    host=os.environ.get("MONGO_HOST")
)

# -----------------------
# Service Model
# -----------------------
# class Service(Document):
#     name = StringField(required=True)
#     title = StringField()
#     description = StringField()  # Optional notes about the service


class Service(Document):
    name = StringField(required=True)
    title = StringField()
    description = StringField()
    image = StringField()   # store image path
    created_at = DateTimeField(default=datetime.datetime.utcnow)
# -----------------------
# Appointment Model
# -----------------------
class Appointment(Document):
    appointment_serial = IntField()
    patient_name = StringField(required=True)
    patient_email = EmailField()
    patient_phone = StringField()
    service = ReferenceField(Service, required=True)
    service_name = StringField(default="")  # denormalized for fast list reads
    date = DateTimeField(required=True)  # date and time combined
    status = StringField(choices=["Pending", "Approved", "Completed", "Cancelled","Delay"], default="Pending")
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    patient = ReferenceField('Patient')

    meta = {
        'indexes': [
            '-appointment_serial',
            'status',
            ('status', '-appointment_serial'),
            'patient_phone',
        ],
    }



# -----------------------
# Review Model
# -----------------------
class Review(Document):
    customer_name = StringField(required=True)
    rating = IntField(min_value=1, max_value=5, required=True)
    comment = StringField()
    created_at = DateTimeField(default=datetime.datetime.utcnow)


# -----------------------
# Before & After Image Model
# -----------------------
# class BeforeAfterImage(Document):
#     service = ReferenceField(Service, required=True)

#     before_image = StringField(required=True)   # image URL / path
#     after_image = StringField(required=True)

#     description = StringField()
#     created_at = DateTimeField(default=datetime.datetime.utcnow)

class GalleryImage(Document):
    """
    Renamed from BeforeAfterImage.
    Single image per record — no before/after categorization.
    """
    service = ReferenceField('Service', required=True)
    # image = StringField(required=True) 
    image = StringField()
    video = StringField()
    description = StringField(default="")
    created_at = DateTimeField(default=datetime.datetime.utcnow)
 
    meta = {
        'collection': 'gallery_images',
        'ordering': ['-created_at'],
    }


class Patient(Document):
    name = StringField(required=True)
    email = EmailField(required=True)
    phone = StringField()
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    patient_serial = IntField()
    appointments = ListField(ReferenceField(Appointment))
    payments = ListField(ReferenceField('Payment'))

    meta = {
        'indexes': [
            '-patient_serial',
            'phone',
            'email',
        ],
    }


# -----------------------
# Payment Model
# -----------------------


class Payment(Document):
    patient = ReferenceField(Patient, required=True)
    appointment = ReferenceField(Appointment)
    amount = FloatField(required=True)
    method = StringField(choices=["Cash", "Card"], default="Cash")
    status = StringField(choices=["Pending", "Paid"], default="Pending")
    created_at = DateTimeField(default=datetime.datetime.utcnow)


# -----------------------
# Review Model (UPDATED)
# -----------------------
class Review(Document):
    # Customer submits these from the website
    customer_name = StringField(required=True)      # ← new: free-form name from website form
    customer_email = EmailField()                    # ← new: optional email
    service = ReferenceField(Service)               # ← new: which service (optional)
    rating = IntField(min_value=1, max_value=5, required=True)
    comment = StringField()
    created_at = DateTimeField(default=datetime.datetime.utcnow)
 
    # Keep this for backward compat if old reviews were linked to appointments
    appointment = ReferenceField(Appointment)



# -----------------------
# Employee Model
# Add this to your existing models.py
# -----------------------
class Employee(Document):
    name = StringField(required=True)
    father_name = StringField()
    id_card_number = StringField()
    designation = StringField()
    department = StringField()
    phone = StringField()
    email = EmailField()
    address = StringField()
    salary = FloatField()
    join_date = StringField()       # stored as "YYYY-MM-DD" string for simplicity
    status = StringField(choices=["Active", "Inactive"], default="Active")
    salary_status = StringField(choices=["Paid", "Unpaid"], default="Unpaid")
    created_at = DateTimeField(default=datetime.datetime.utcnow)
 

# -----------------------
# Supplier Model
# Add to models.py
# -----------------------
class Supplier(Document):
    name = StringField(required=True)
    contact_person = StringField()
    phone = StringField()
    email = EmailField()
    address = StringField()
    created_at = DateTimeField(default=datetime.datetime.utcnow)
 
 
# -----------------------
# Inventory Item Model
# Add to models.py
# -----------------------
class InventoryItem(Document):
    name = StringField(required=True)
    category = StringField(
        choices=["Consumable", "Medicine", "Equipment", "Instrument", "Other"],
        required=True
    )
    quantity = FloatField(default=0)
    unit = StringField(default="pieces")          # boxes, pieces, ml, etc.
    cost_price = FloatField(default=0)
    supplier_name = StringField()                 # quick ref — no FK needed
    supplier = ReferenceField('Supplier')         # optional link to Supplier doc
    expiry_date = StringField()                   # stored as "YYYY-MM-DD"
    low_stock_threshold = FloatField(default=10)  # admin sets per item
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)


# -----------------------
# Expense Model
# Add to models.py
# -----------------------
class Expense(Document):
    title = StringField(required=True)           # e.g. "March Rent", "Electricity Bill"
    category = StringField(
        choices=["Salary", "Inventory", "Rent", "Utilities", "Maintenance", "Other"],
        required=True
    )
    amount = FloatField(required=True)
    month = StringField()                        # "2026-03" format for grouping
    note = StringField()                         # optional description
    created_at = DateTimeField(default=datetime.datetime.utcnow)
 



 
# -----------------------
# Prescription Model
# -----------------------
class Prescription(Document):
    """
    Stores a doctor's prescription for a patient.
    medicines_text is a free-form field — the doctor can write
    medicine names, dosages, durations, and notes in any format.
    """
    patient         = ReferenceField('Patient', required=True)
    appointment     = ReferenceField('Appointment')          # optional link
 
    # Core free-form fields
    medicines_text  = StringField(required=True)             # full prescription body
    referred_by     = StringField(default="")               # doctor name
    chief_complaint = StringField(default="")               # patient's complaint
    diagnosis       = StringField(default="")               # doctor's diagnosis notes
 
    # Auto timestamps
    created_at      = DateTimeField(default=datetime.datetime.utcnow)
    updated_at      = DateTimeField(default=datetime.datetime.utcnow)
 
    meta = {
        'collection': 'prescriptions',
        'ordering':   ['-created_at'],
    }
 
 
# -----------------------
# Treatment History Model
# -----------------------
class TreatmentHistory(Document):
    """
    Stores dental procedures and work done for a patient.
    treatment_text is a free-form field so the doctor can describe
    any procedure in their own format without being restricted to
    fixed fields.
    """
    patient         = ReferenceField('Patient', required=True)
    appointment     = ReferenceField('Appointment')          # optional link
 
    # Core free-form fields
    treatment_text  = StringField(required=True)             # full procedure notes
    handled_by      = StringField(default="")               # doctor/staff name
    procedure_type  = StringField(default="")               # e.g. RCT, Scaling, Extraction
 
    # Auto timestamps
    created_at      = DateTimeField(default=datetime.datetime.utcnow)
    updated_at      = DateTimeField(default=datetime.datetime.utcnow)
 
    meta = {
        'collection': 'treatment_history',
        'ordering':   ['-created_at'],
    }




# -----------------------
# Billing Record Model
# One per patient (tracks the total treatment cost)
# -----------------------
class BillingRecord(Document):
    """
    Represents the overall billing for a patient's treatment.
    Created once per treatment course (e.g. Braces = PKR 80,000 total).
    Installments are recorded separately in the Installment model.
    """
    patient      = ReferenceField('Patient', required=True)
    total_cost   = FloatField(required=True, default=0)     # set by admin
    service_name = StringField(default="")                  # e.g. "Braces Treatment"
    notes        = StringField(default="")                  # billing notes
 
    # Auto timestamps
    created_at   = DateTimeField(default=datetime.datetime.utcnow)
    updated_at   = DateTimeField(default=datetime.datetime.utcnow)
 
    meta = {
        'collection': 'billing_records',
        'ordering':   ['-created_at'],
    }
 
 
# -----------------------
# Installment Model
# Each payment entry (partial or full) by the patient
# -----------------------
class Installment(Document):
    """
    A single payment entry against a BillingRecord.
    Supports full, partial, and installment-based payments.
    """
    patient        = ReferenceField('Patient', required=True)
    billing        = ReferenceField('BillingRecord', required=True)
    appointment    = ReferenceField('Appointment')              # optional
 
    amount         = FloatField(required=True)                  # amount paid this entry
    balance_after  = FloatField(default=0)                      # remaining due after this payment
    method         = StringField(
        choices=["Cash", "Online Transfer", "Card", "Cheque"],
        default="Cash"
    )
    service_name   = StringField(default="")                    # session-specific service
    notes          = StringField(default="")                    # optional notes
 
    # Auto timestamps
    created_at     = DateTimeField(default=datetime.datetime.utcnow)
    updated_at     = DateTimeField(default=datetime.datetime.utcnow)
 
    meta = {
        'collection': 'installments',
        'ordering':   ['-created_at'],
    }


"""
security/models.py
──────────────────
MongoEngine models for MongoDB collections:
  - UserProfile   : extended user info (phone, clinic, role, 2FA settings)
  - OTPCode       : one-time passwords for SMS / Email 2FA flows
  - UserSession   : manual session tracking for "log out all" support
"""

from mongoengine import Document, StringField, BooleanField, DateTimeField, IntField, ListField, ReferenceField
from datetime import datetime, timedelta
import secrets
import string
from django.utils import timezone  # Still use Django's timezone if needed




# ─────────────────────────────────────────────────────────────────────────────
#  UserProfile
#  Stores profile extras and notification preferences.
#  All 2FA fields have been removed.
# ─────────────────────────────────────────────────────────────────────────────
class UserProfile(Document):
    """Extended profile stored in MongoDB."""
 
    user_id = StringField(max_length=64, unique=True, required=True, db_field="user_id")
 
    # ── Personal info ─────────────────────────────────────────────────────
    full_name = StringField(max_length=150, default="")
    username  = StringField(max_length=150, default="")
    email     = StringField(max_length=254, default="")
    phone     = StringField(max_length=30,  default="")
    clinic    = StringField(max_length=150, default="Dentistree Clinic")
    role      = StringField(max_length=100, default="")
    photo     = StringField(default="")        # base64 or URL
 
    # ── Notification preferences ─────────────────────────────────────────
    notif_new_appointments = BooleanField(default=True)
    notif_reminders        = BooleanField(default=True)
    notif_reviews          = BooleanField(default=False)
    notif_inventory        = BooleanField(default=True)
    notif_reports          = BooleanField(default=False)
    notif_system_alerts    = BooleanField(default=True)
    notif_staff_updates    = BooleanField(default=False)
    notif_invoices         = BooleanField(default=True)
 
    # ── Django role mirrors ───────────────────────────────────────────────
    is_superuser = BooleanField(default=False)
    is_staff     = BooleanField(default=False)
 
    # ── Meta ──────────────────────────────────────────────────────────────
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
 
    meta = {
        'collection': 'user_profiles',
        'strict': False,   # ignore legacy 2FA fields still in DB documents
        'indexes': [
            'user_id',
            'email',
            'username',
        ]
    }
 
    def __str__(self):
        return f"UserProfile(user_id={self.user_id}, username={self.username})"
 
    def to_dict(self):
        return {
            "user_id":   self.user_id,
            "full_name": self.full_name,
            "username":  self.username,
            "email":     self.email,
            "phone":     self.phone,
            "clinic":    self.clinic,
            "role":      self.role,
            "photo":     self.photo,
            "notifications": {
                "newAppointments": self.notif_new_appointments,
                "reminders":       self.notif_reminders,
                "reviews":         self.notif_reviews,
                "inventory":       self.notif_inventory,
                "reports":         self.notif_reports,
                "systemAlerts":    self.notif_system_alerts,
                "staffUpdates":    self.notif_staff_updates,
                "invoices":        self.notif_invoices,
            },
            "is_superuser": self.is_superuser,
            "is_staff":     self.is_staff,
        }
 
    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  OTPCode
#  Retained so that delete_account can clean up any lingering OTP records.
# ─────────────────────────────────────────────────────────────────────────────
OTP_PURPOSE_CHOICES = [
    ("email_verify", "Email Verification"),
    ("phone_verify", "Phone Verification"),
]
 
class OTPCode(Document):
    user_id    = StringField(max_length=64, required=True, db_field="user_id")
    purpose    = StringField(max_length=20, choices=[c[0] for c in OTP_PURPOSE_CHOICES], required=True)
    code       = StringField(max_length=8, required=True)
    is_used    = BooleanField(default=False)
    expires_at = DateTimeField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)
 
    meta = {
        'collection': 'otp_codes',
        'indexes': [
            'user_id',
            'purpose',
            ('user_id', 'purpose', 'is_used'),
        ]
    }
 
    @classmethod
    def generate(cls, user_id: str, purpose: str, length: int = 6, ttl_minutes: int = 10):
        cls.objects(user_id=user_id, purpose=purpose, is_used=False).update(is_used=True)
        code = "".join(secrets.choice(string.digits) for _ in range(length))
        otp = cls(
            user_id=user_id,
            purpose=purpose,
            code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes),
        )
        otp.save()
        return otp
 
    @classmethod
    def verify(cls, user_id: str, purpose: str, code: str) -> bool:
        try:
            otp = cls.objects.get(user_id=user_id, purpose=purpose, code=code, is_used=False)
        except cls.DoesNotExist:
            return False
        if datetime.utcnow() > otp.expires_at:
            otp.is_used = True
            otp.save()
            return False
        otp.is_used = True
        otp.save()
        return True
 
    def __str__(self):
        return f"OTP({self.purpose}, user={self.user_id}, used={self.is_used})"
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  NotificationSchedulerState
# ─────────────────────────────────────────────────────────────────────────────
class NotificationSchedulerState(Document):
    job_key     = StringField(max_length=60, unique=True, required=True)
    last_run_at = DateTimeField(default=datetime.utcnow)
 
    meta = {"collection": "notification_scheduler_state"}
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  AdminNotification
# ─────────────────────────────────────────────────────────────────────────────
class AdminNotification(Document):
    notification_type = StringField(max_length=40, required=True)
    title             = StringField(max_length=200, required=True)
    message           = StringField(max_length=500, default="")
    link_page         = StringField(max_length=60,  default="")
    link_item_id      = StringField(max_length=100, default="")
    is_read           = BooleanField(default=False)
    created_at        = DateTimeField(default=datetime.utcnow)
 
    meta = {
        'collection': 'admin_notifications',
        'indexes': ['-created_at', 'is_read', 'notification_type'],
        'ordering': ['-created_at'],
    }
 
    def to_feed_dict(self):
        return {
            "id":           str(self.id),
            "type":         self.notification_type,
            "title":        self.title,
            "message":      self.message,
            "link_page":    self.link_page or "",
            "link_item_id": self.link_item_id or "",
            "is_read":      self.is_read,
            "created_at":   self.created_at.isoformat() if self.created_at else None,
        }
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  UserSession
# ─────────────────────────────────────────────────────────────────────────────
class UserSession(Document):
    user_id       = StringField(max_length=64, required=True, db_field="user_id")
    session_key   = StringField(max_length=40, unique=True, required=True)
    ip_address    = StringField(max_length=45,  default="")
    user_agent    = StringField(max_length=300, default="")
    created_at    = DateTimeField(default=datetime.utcnow)
    last_activity = DateTimeField(default=datetime.utcnow)
    is_active     = BooleanField(default=True)
 
    meta = {
        'collection': 'user_sessions',
        'indexes': [
            'user_id',
            'session_key',
            ('user_id', 'is_active'),
        ]
    }
 
    def save(self, *args, **kwargs):
        self.last_activity = datetime.utcnow()
        return super().save(*args, **kwargs)
 
    def __str__(self):
        return f"UserSession(user={self.user_id}, key={self.session_key[:8]}…, active={self.is_active})"
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  CookieConsentLog
# ─────────────────────────────────────────────────────────────────────────────
class CookieConsentLog(Document):
    visitor_id       = StringField(max_length=64, required=True)
    necessary        = BooleanField(default=True)
    analytics        = BooleanField(default=False)
    functional       = BooleanField(default=False)
    marketing        = BooleanField(default=False)
    consent_version  = StringField(default="1.0")
    action           = StringField(
        choices=["accept_all", "reject_non_essential", "save_preferences"],
        default="save_preferences",
    )
    user_agent  = StringField(max_length=300, default="")
    ip_address  = StringField(max_length=45,  default="")
    created_at  = DateTimeField(default=datetime.utcnow)
 
    meta = {
        "collection": "cookie_consent_logs",
        "indexes": ["visitor_id", "-created_at"],
    }