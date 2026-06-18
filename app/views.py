from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
import json
# import datetime
from bson import ObjectId
import pytz
from datetime import datetime, timedelta, date
import re
# from datetime import datetime, timedelta
from .models import Service, Appointment, Payment, Review, Patient, UserProfile, AdminNotification
from .notification_utils import (
    notify_new_appointment,
    notify_new_review,
    notify_low_inventory,
)


# =======================
# SERVICE CRUD
# ======================

# @csrf_exempt
# def create_service(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)


#             name = data.get("name")
#             title = data.get("title")
#             description = data.get("description")
#             # image = request.FILES.get("image")

#             if not name:
#                 return JsonResponse({"error": "Name is required"}, status=400)

#             # image_path = ""
#             # if image:
#             #     file_path = f"media/{image.name}"
#             #     with open(file_path, "wb+") as destination:
#             #         for chunk in image.chunks():
#             #             destination.write(chunk)
#             #     image_path = "/" + file_path

#             Service.objects.create(
#                 name=name,
#                 title=title,
#                 description=description,
#                 image=""
#             ).save()

#             return JsonResponse({"message": "Created"}, status=201)

#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def create_service(request):
    if request.method == "POST":
        try:
            # Change this: Get text from request.POST instead of json.loads
            name = request.POST.get("name")
            title = request.POST.get("title")
            description = request.POST.get("description")
            image = request.FILES.get("image") # Get file from FILES
            

            
            if not name:
                return JsonResponse({"error": "Name is required"}, status=400)

            image_path = ""
            if image:
                # Save the image to the media folder
                import os
                from django.conf import settings
                
                # Create directory if it doesn't exist
                upload_dir = os.path.join(settings.MEDIA_ROOT, "services")
                os.makedirs(upload_dir, exist_ok=True)
                
                # Save file
                file_path = os.path.join(upload_dir, image.name)
                with open(file_path, "wb+") as destination:
                    for chunk in image.chunks():
                        destination.write(chunk)
                image_path = f"/media/services/{image.name}"

            Service.objects.create(
                name=name,
                title=title,
                description=description,
                image=image_path
            ).save()

            return JsonResponse({"message": "Created"}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


def get_services(request):
    services = Service.objects()

    data = []
    for s in services:
        data.append({
            "id": str(s.id),
            "name": s.name,
            "title": s.title,
            "description": s.description,
            "image": s.image,
            "created_at": s.created_at.isoformat() if s.created_at else None

        })

    return JsonResponse(data, safe=False)
# @csrf_exempt
# def update_service(request, id):
#     if request.method == "POST":
#         data = json.loads(request.body)

#         service = Service.objects(id=id).first()
#         service.name = data.get("name")
#         service.title = data.get("title")
#         service.description = data.get("description")
#         service.save()

#         return JsonResponse({"message": "Service updated"})

@csrf_exempt
def update_service(request, id):
    if request.method == "POST":
        try:
            service = Service.objects(id=id).first()
            if not service:
                return JsonResponse({"error": "Not found"}, status=404)

            # Use request.POST for text fields
            service.name = request.POST.get("name", service.name)
            service.title = request.POST.get("title", service.title)
            service.description = request.POST.get("description", service.description)

            # Handle new image upload
            image = request.FILES.get("image")
            if image:
                import os
                from django.conf import settings
                file_path = os.path.join(settings.MEDIA_ROOT, "services", image.name)
                with open(file_path, "wb+") as destination:
                    for chunk in image.chunks():
                        destination.write(chunk)
                service.image = f"/media/services/{image.name}"

            service.save()
            return JsonResponse({"message": "Service updated"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def delete_service(request, id):
    if request.method == "POST":
        service = Service.objects(id=id).first()
        if not service:
            return JsonResponse({"error": "Service not found"}, status=404)
        service.delete()
        return JsonResponse({"message": "Service deleted"})


# =======================
# APPOINTMENT
# =======================

# @csrf_exempt
# def create_appointment(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             phone = data.get("patient_phone")
#             name = data.get("patient_name")
#             email = data.get("patient_email")
            

#             clean_phone = re.sub(r'\D', '', str(phone))
#             if len(clean_phone) != 11:
#                 return JsonResponse({"error": "Phone must be exactly 11 digit."}, status=400)
            
#             # It is necessary to find the Service object by ID first
#             service_obj = Service.objects(id=data.get("service")).first()
            
#             if not service_obj:
#                 return JsonResponse({"error": "Service ID is invalid or not found"}, status=404)
            
#             patient = Patient.objects(phone=phone).first()

#             if not patient:
#                 last_p = Patient.objects.order_by('-patient_serial').first()
#                 new_p_serial = (last_p.patient_serial + 1) if last_p and last_p.patient_serial else 1
#                 patient = Patient(
#                     name = name,
#                     email = email,
#                     phone = phone
#                 )
#                 patient.save()
            
#             assigned_serial = patient.patient_serial
#             tz = pytz.timezone("Asia/Karachi")

#             naive_date = datetime.strptime(data.get("date"), "%Y-%m-%d %H:%M")
#             aware_date = tz.localize(naive_date)

#             last_appt = Appointment.objects(appointment_serial__exists=True,
#                                             appointment_serial__ne=None ).order_by('-appointment_serial').first()
#             new_serial = (last_appt.appointment_serial + 1) if last_appt and last_appt.appointment_serial else 1
            

#             appointment = Appointment(
#             appointment_serial=assigned_serial,
#             patient_name=patient.name,
#             patient_email=patient.email,
#             patient_phone=patient.phone,
#             service=service_obj,
#             date=aware_date,
#             status="pending"
# ).save()

#             return JsonResponse({
#                 "message": "Appointment created successfully!", 
#                 "patient_serial":assigned_serial,
#                 "id":str(appointment.id)
#                 # "id": str(appointment.id),
#                 # "appointment_serial": appointment.appointment_serial   
#             }, status=201)
            
#         except ValueError:
#             return JsonResponse({
#                 "error": "Invalid date format! Please use YYYY-MM-DD HH:MM (e.g., 2026-04-03 14:30)"
#             }, status=400)
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)
    
#     return JsonResponse({"error": "Only POST requests are allowed"}, status=405)




# @csrf_exempt
# def create_appointment(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             phone = str(data.get("patient_phone", "")).strip()
#             name = data.get("patient_name")
#             email = data.get("patient_email")

#             # 1. Phone number validation
#             clean_phone = re.sub(r'\D', '', phone)
#             if len(clean_phone) != 11:
#                 return JsonResponse({"error": "Phone must be exactly 11 digits."}, status=400)
            
#             # Service check
#             service_id = data.get("service")
#             service_obj = Service.objects(id=service_id).first()
#             if not service_obj:
#                 return JsonResponse({"error": "Service ID is invalid"}, status=404)

#             # 2. CONSISTENCY CHECK: Pehle Patient dhoondo Phone Number se
#             patient = Patient.objects(phone=clean_phone).first()

#             if not patient:
#                 # NAYA PATIENT: Serial number generate karein
#                 last_p = Patient.objects.order_by('-patient_serial').first()
#                 new_p_serial = (last_p.patient_serial + 1) if last_p and last_p.patient_serial else 1
                
#                 patient = Patient(
#                     name=name,
#                     email=email,
#                     phone=clean_phone,
#                     patient_serial=new_p_serial  # Registration ID yahan save hogi
#                 )
#                 patient.save()
            
#             # 3. ASSIGNED SERIAL: Ye hamesha purani ID hogi agar patient purana hai
#             # Agar purane patient record mein serial missing hai, toh fallback to ID
#             assigned_serial = getattr(patient, 'patient_serial', 1)

#             # Timezone handling
#             tz = pytz.timezone("Asia/Karachi")
#             naive_date = datetime.strptime(data.get("date"), "%Y-%m-%d %H:%M")
#             aware_date = tz.localize(naive_date)

#             # 4. SAVE APPOINTMENT: 
#             # Hum Appointment serial ko Patient serial ke barabar kar rahe hain
#             appointment = Appointment(
#                 appointment_serial=assigned_serial, # PURANI ID USE HO RAHI HAI
#                 patient_name=patient.name,
#                 patient_email=patient.email,
#                 patient_phone=patient.phone,
#                 service=service_obj,
#                 date=aware_date,
#                 status="Pending"
#             )
#             appointment.save()

#             return JsonResponse({
#                 "message": "Appointment created successfully!", 
#                 "patient_serial": assigned_serial, # Frontend check ke liye
#                 "id": str(appointment.id)
#             }, status=201)

#         except Exception as e:
#             # 500 error ki exact wajah yahan se pata chalegi
#             return JsonResponse({"error": str(e)}, status=500)
    
#     return JsonResponse({"error": "Only POST allowed"}, status=405)


@csrf_exempt
def create_appointment(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            phone = str(data.get("patient_phone", "")).strip()
            name  = data.get("patient_name", "").strip()
            email = data.get("patient_email", "").strip()

            # 1. Phone validation
            clean_phone = re.sub(r'\D', '', phone)
            if len(clean_phone) != 11:
                return JsonResponse({"error": "Phone must be exactly 11 digits."}, status=400)

            # 2. Service check
            service_id  = data.get("service")
            service_obj = Service.objects(id=service_id).first()
            if not service_obj:
                return JsonResponse({"error": "Service ID is invalid"}, status=404)

            # 3. Date parsing — do this before any DB write so an invalid
            #    date can't leave behind an orphaned patient record
            tz         = pytz.timezone("Asia/Karachi")
            naive_date = datetime.strptime(data.get("date"), "%Y-%m-%d %H:%M")
            aware_date = tz.localize(naive_date)

            # 4. Find or create patient
            patient = Patient.objects(phone=clean_phone).first()

            if not patient:
                last_p       = Patient.objects.order_by('-patient_serial').first()
                new_p_serial = (last_p.patient_serial + 1) if last_p and last_p.patient_serial else 1

                patient = Patient(
                    name=name,
                    email=email if email else None,   # ← don't pass empty string to EmailField
                    phone=clean_phone,
                    patient_serial=new_p_serial
                )
                patient.save()

            assigned_serial = patient.patient_serial or 1

            # 5. Create appointment — FIX: set patient reference
            appointment = Appointment(
                appointment_serial=assigned_serial,
                patient=patient,                      # ← Bug 2 fix: link the patient
                patient_name=patient.name,
                patient_email=patient.email,
                patient_phone=patient.phone,
                service=service_obj,
                service_name=service_obj.name,
                date=aware_date,
                status="Pending",
            )
            appointment.save()

            # 6. FIX: append appointment to patient's list
            patient.appointments.append(appointment)  # ← Bug 3 fix
            patient.save()

            try:
                appt_label = aware_date.strftime("%d %b %Y, %I:%M %p")
                notify_new_appointment(
                    patient.name or name,
                    service_obj.name,
                    appt_label,
                )
            except Exception:
                pass

            service_map = {str(service_obj.id): service_obj.name}
            row = serialize_appointment(appointment, service_map)

            return JsonResponse({
                "message": "Appointment created successfully!",
                "patient_serial": assigned_serial,
                "appointment_serial": assigned_serial,
                "id": str(appointment.id),
                "appointment": row,
            }, status=201)

        except ValueError:
            return JsonResponse(
                {"error": "Invalid date format. Use YYYY-MM-DD HH:MM (e.g. 2026-04-03 14:30)"},
                status=400
            )
        except Exception:
            import traceback
            print(traceback.format_exc())  # full traceback to server logs only
            return JsonResponse(
                {"error": "Something went wrong creating the appointment."},
                status=500,
            )

    return JsonResponse({"error": "Only POST allowed"}, status=405)





from django.http import JsonResponse

from django.http import JsonResponse

# def get_appointments(request):
#     try:
#         appointments = Appointment.objects  # MongoEngine QuerySet

#         data = []
#         for a in appointments:
#             # 🔹 Safe service dereference
#             try:
#                 service_name = a.service.name
#             except:
#                 service_name = None

#             # 🔹 Safe date conversion
#             try:
#                 date_str = str(a.date)
#             except:
#                 date_str = None

#             # 🔹 Build appointment dict
#             data.append({
#                 "id": str(a.id),
#                 "patient_serial": getattr(a.patient.patient_serial,None) if a.patient else None, # Add this
#                 "patient_name": getattr(a, "patient_name", None),
#                 "email": getattr(a, "patient_email", None),
#                 "phone": getattr(a, "patient_phone", None),
#                 "service": service_name,
#                 "date": date_str,
#                 "status": getattr(a, "status", None)
#             })

#         return JsonResponse(data, safe=False)

    # except Exception as e:
    #     # Agar kuch unexpected ho jaye, exact error Postman me dikhe
    #     return JsonResponse({"error": str(e)})
# @csrf_exempt
# def get_appointments(request):
#     try:
#         # appointments = Appointment.objects.all().order_by('-date')
#         appointments = Appointment.objects.order_by('-date')
#         data = []
#         for a in appointments:
#             # Check karein ke service object exist karta hai ya nahi
#             # service_name = a.service.name if a.service else "General Service"
#             try:
#                 service_name = a.service.name
#             except:
#                 service_name = "General Service"



#             # Date formatting check karein
#             date_str = a.date.strftime('%Y-%m-%d %H:%M') if a.date else "No Date"

#             data.append({
#                 "id": str(a.id),
#                 # Yahan getattr ko mazeed safe banayein
#                 # "patient_serial": getattr(a.patient, 'patient_serial', None) if getattr(a, 'patient', None) else None,
#                 "patient_serial":a.appointment_serial,
#                 "patient_name": a.patient_name,
#                 "email": a.patient_email,
#                 "phone": a.patient_phone,
#                 "service": service_name,
#                 "date": date_str,
#                 "status": a.status
#             })
#         return JsonResponse(data, safe=False)
#     except Exception as e:
#         # Agar koi backend error hai toh wo response mein nazar aayega
#         return JsonResponse({"error": str(e)}, status=500)


from .appointment_helpers import (
    fetch_appointments_list,
    appointments_poll_token,
    serialize_appointment,
    build_service_map,
    sort_appointment_rows,
)


@csrf_exempt
def get_appointments(request):
    """Optimized list: indexed queries, field projection, batch service lookup."""
    try:
        limit = request.GET.get("limit", 500)
        data = fetch_appointments_list(limit=limit)
        return JsonResponse(data, safe=False, status=200)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def appointments_poll_view(request):
    """Lightweight poll — admin UI refreshes when version changes."""
    try:
        return JsonResponse(appointments_poll_token())
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
import json

from .models import Appointment


# @csrf_exempt
# def update_appointment_status(request, id):
#     if request.method != "POST":
#         return JsonResponse({"error": "Only POST allowed"}, status=405)

#     try:
#         data = json.loads(request.body)
#         status = data.get("status")  # Approved / Rejected / Delay

#         if status not in ["Approved", "Cancelled"]:
#             return JsonResponse({"error": "Invalid status"}, status=400)

#         appointment = Appointment.objects(id=id).first()
#         if not appointment:
#             return JsonResponse({"error": "Appointment not found"}, status=404)

#         if appointment.status != "Pending":
#             return JsonResponse({"error": "Status already updated"}, status=400)

#         appointment.status = status
#         appointment.save()

#         # Auto add patient if approved
#         if status == "Approved":
#             patient = Patient.objects(id=ObjectId(data.get("patient_id"))).first()
#             if not patient:
#                 patient = Patient(
#                     name=appointment.patient_name,
#                     email=appointment.patient_email,
#                     phone=appointment.patient_phone,
#                     appointments = [appointment]
#                 ).save()
#             else:
#                 if appointment not in patient.appointments:
#                     patient.appointments.append(appointment)
#                     patient.save()

#             # Optional: Auto link appointment to patient
#             appointment.patient = patient
#             appointment.save()

#         # Email Notification (professional message)
#         if appointment.patient_email:
#             email_subject = "Appointment Status Update"
#             if status == "Approved":
#                 email_message = f"Dear {appointment.patient_name},\n\nYour appointment has been approved for {appointment.date.strftime('%Y-%m-%d %H:%M')}.\n\nThank you!"
#             elif status == "Rejected":
#                 email_message = f"Dear {appointment.patient_name},\n\nWe are sorry, your appointment has been rejected. Please contact us for details."
#             else:  # Delay
#                 email_message = f"Dear {appointment.patient_name},\n\nYour appointment is delayed. We will call you for rescheduling.\n\nThank you!"

#             send_mail(
#                 subject=email_subject,
#                 message=email_message,
#                 from_email="rababzahra425@gmail.com",
#                 recipient_list=[appointment.patient_email],
#                 fail_silently=True
#             )

#         return JsonResponse({"message": "Status updated & email sent"})

#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def update_appointment_status(request, id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)
        status = data.get("status")  # Approved / Cancelled / Delay

        # 1. FIXED: List mein 'Delay' shamil kar diya
        if status not in ["Approved", "Cancelled", "Delay"]:
            return JsonResponse({"error": "Invalid status value"}, status=400)

        appointment = Appointment.objects(id=id).first()
        if not appointment:
            return JsonResponse({"error": "Appointment not found"}, status=404)

        # 2. IMPORTANT: Check if already processed (taake bar bar email na jaye)
        if appointment.status != "Pending":
            return JsonResponse({"error": "This appointment has already been processed."}, status=400)

        appointment.status = status
        appointment.save()

        # 3. Patient Linking (Only for Approved)
        if status == "Approved" and not appointment.patient:
            # from .models import Patient
            # patient = Patient.objects(email=appointment.patient_email).first()
            # if not patient:
            #     last_patient_count = Patient.objects().count()
            #     new_serial = last_patient_count + 1

            #     patient = Patient(
            #         id=appointment.id,
            #         name=appointment.patient_name,
            #         email=appointment.patient_email,
            #         phone=appointment.patient_phone,
            #         patient_serial=new_serial
            #     ).save(force_insert=True)
            # appointment.patient = patient
            # appointment.save()

            from .models import Patient
            patient = Patient.objects(email=appointment.patient_email).first()
            
            # if not patient:
            #     last_patient_count = Patient.objects().count()
            #     new_serial = last_patient_count + 1

            #     patient = Patient(
            #         id=appointment.id,
            #         name=appointment.patient_name,
            #         email=appointment.patient_email,
            #         phone=appointment.patient_phone,
            #         patient_serial=new_serial,
            #         appointments=[appointment] 
            #     ).save(force_insert=True)
            if not patient:
                last_patient = Patient.objects().order_by('-patient_serial').first()
                new_serial = (last_patient.patient_serial + 1) if last_patient and last_patient.patient_serial else 1

                patient = Patient(
                    name=appointment.patient_name,
                    email=appointment.patient_email,
                    phone=appointment.patient_phone,
                    patient_serial=new_serial, # Yahan serial number save ho raha hai
                    appointments=[appointment]
                    ).save()
            else:
                # Agar patient pehle se hai, to naye appointment ko list mein add karein
                if appointment not in patient.appointments:
                    patient.appointments.append(appointment)
                    patient.save()

            # Appointment ko patient se link karein
            appointment.patient = patient
            appointment.save()

        # 4. EMAIL LOGIC
        if appointment.patient_email:
            try:
                _send_appointment_email(appointment, status)
            except Exception as mail_err:
                print(f"EMAIL ERROR: {mail_err}")

        return JsonResponse({"message": "Status updated successfully!"})

    except Exception as e:
        print(f"Server Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


# views.py me ye add karein
@csrf_exempt
def delete_appointment(request, id):
    if request.method == "DELETE":
        Appointment.objects(id=id).delete()
        return JsonResponse({"message": "Deleted successfully"})

@csrf_exempt
def edit_appointment(request, id):
    if request.method == "POST":
        data = json.loads(request.body)
        appointment = Appointment.objects(id=id).first()
        if appointment:
            appointment.patient_name = data.get("patient_name", appointment.patient_name)
            # baqi fields bhi update karein...
            appointment.save()
            return JsonResponse({"message": "Updated successfully"})



# =======================
# PAYMENT (Receptionist Flow)
# =======================

@csrf_exempt
def create_payment(request):
    if request.method == "POST":
        data = json.loads(request.body)

        appointment = Appointment.objects(id=data.get("appointment_id")).first()

        payment = Payment(
            appointment=appointment,
            amount=data.get("amount"),
            method=data.get("method", "Cash"),
            status="Paid"
        ).save()

        return JsonResponse({"message": "Payment added"})


# def get_payments(request):
#     payments = Payment.objects()

#     data = []
#     for p in payments:
#         data.append({
#             "id": str(p.id),
#             "patient": p.appointment.patient_name if p.appointment else None,
#             "amount": p.amount,
#             "method": p.method,
#             "status": p.status,
#             "date": p.created_at
#         })

#     return JsonResponse(data, safe=False)
from mongoengine.errors import DoesNotExist

def get_payments(request):
    """
    Fetches payments. If patient_id query param is present, filters by that patient.
    Safely bypasses broken appointment or patient DBRefs to prevent 500 crashes.
    """
    try:
        patient_id = request.GET.get("patient_id")
        
        if patient_id:
            # Safe parsing key logic matching patient references
            payments = Payment.objects(patient=patient_id)
        else:
            payments = Payment.objects()

        data = []
        for p in payments:
            patient_name = "Unknown Patient"
            
            # ─── SAFE REFERENTIAL CHECK FOR PATIENT & APPOINTMENT ───
            try:
                if p.patient:
                    patient_name = p.patient.name
                elif p.appointment:
                    patient_name = p.appointment.patient_name
            except DoesNotExist:
                patient_name = "Patient Record Deleted"
            except Exception:
                pass

            # Safe invoice date conversion check
            date_str = p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "—"

            data.append({
                "id": str(p.id),
                "patient": patient_name,
                "amount": p.amount,
                "method": p.method,
                "status": p.status,
                "date": date_str
            })

        return JsonResponse(data, safe=False, status=200)
        
    except Exception as e:
        print(f"Payments Fetch Crash: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def create_or_update_payment(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        data = json.loads(request.body)
        patient = Patient.objects(id=data.get("patient_id")).first()
        if not patient:
            return JsonResponse({"error": "Patient not found"}, status=404)

        # ✅ Resolve Appointment object first
        appt_id = data.get("appointment_id")
        appt = Appointment.objects(id=appt_id).first() if appt_id else None

        # ✅ Query with proper object, not raw string
        payment = Payment.objects(patient=patient, appointment=appt).first()

        if not payment:
            payment = Payment(
                patient=patient,
                appointment=appt,
                amount=data.get("amount", 0),
                method=data.get("method", "Cash"),
                status=data.get("status", "Pending")
            ).save()
            # ✅ Link payment back to patient
            patient.payments.append(payment)
            patient.save()
        else:
            payment.amount = data.get("amount", payment.amount)
            payment.method = data.get("method", payment.method)
            payment.status = data.get("status", payment.status)
            payment.save()

        return JsonResponse({"message": "Payment saved successfully"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# =======================
# FINANCIAL REPORT
# =======================

def financial_report(request):
    payments = Payment.objects(status="Paid")

    total = sum([p.amount for p in payments])

    data = []
    for p in payments:
        data.append({
            "patient": p.appointment.patient_name,
            "amount": p.amount,
            "date": p.created_at
        })

    return JsonResponse({
        "total_earnings": total,
        "transactions": data
    })



        

@csrf_exempt
def create_patient(request):
    if request.method == "POST":
        data = json.loads(request.body)

        patient = Patient(
            name=data.get("name"),
            email=data.get("email"),
            phone=data.get("phone")
        ).save()

        return JsonResponse({"message": "Patient added"})
    




# def get_patients(request):
#     try:
#         # Saare patients uthayen
#         patients = Patient.objects.all()

#         data = []
#         for p in patients:
#             appointment_data = []
            
#             # Agar patient ke appointments hain
#             if hasattr(p, 'appointments') and p.appointments:
#                 for a in p.appointments:
#                     # 1. Pehle dekho appointment object theek hai?
#                     if not a: continue
                    
#                     # 2. Service ka naam nikalne ka sab se safe tareeqa
#                     s_name = "General Checkup" # Default
#                     try:
#                         if a.service:
#                             s_name = a.service.name
#                     except:
#                         s_name = "Service Not Found"

#                     appointment_data.append({
#                         "id": str(a.id),
#                         "service": s_name, # Ab ye "Checkup" nahi asli naam dega
#                         "date": str(a.date) if a.date else "",
#                         "status": getattr(a, "status", "Pending")
#                     })

#             payment_data = []
#             if hasattr(p, 'payments') and p.payments:
#                 for pay in p.payments:
#                     if not pay: continue
#                     payment_data.append({
#                         "id": str(pay.id),
#                         "amount": pay.amount,
#                         "method": pay.method,
#                         "status": pay.status
#                     })

#             data.append({
#                 "id": str(p.id),
#                 "name": p.name,
#                 "email": p.email,
#                 "phone": p.phone,
#                 "appointments": appointment_data,
#                 "payments": payment_data
#             })

#         return JsonResponse(data, safe=False)

#     except Exception as e:
#         # Error console mein print hoga taake aap dekh saken
#         print(f"PATIENT API ERROR: {str(e)}")
#         return JsonResponse({"error": str(e)}, status=500)
    


# ══════════════════════════════════════════════════════════════════
#  PATIENT CRUD — paste these views into your views.py
#  (replace the existing create_patient / get_patients blocks)
# ══════════════════════════════════════════════════════════════════
 
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Patient, Appointment, Payment
 
 
# ─── CREATE patient (manual "Add Patient" form) ────────────────
@csrf_exempt
def create_patient(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        data = json.loads(request.body)
 
        name  = data.get("name", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
 
        if not name or not email:
            return JsonResponse({"error": "Name and email are required"}, status=400)
 
        # Prevent duplicate email
        if Patient.objects(email=email).first():
            return JsonResponse({"error": "A patient with this email already exists"}, status=400)
 
        # Auto-increment serial
        last = Patient.objects(
            patient_serial__exists=True,
            patient_serial__ne=None
        ).order_by('-patient_serial').first()
        new_serial = (last.patient_serial + 1) if last else 1
 
        patient = Patient(
            name=name,
            email=email,
            phone=phone,
            patient_serial=new_serial,
        )
        patient.save()
 
        return JsonResponse({
            "message": "Patient created successfully",
            "id": str(patient.id),
            "patient_serial": patient.patient_serial,
        }, status=201)
 
    except Exception as e:
        print(f"CREATE PATIENT ERROR: {e}")
        return JsonResponse({"error": str(e)}, status=500)
 
 
# ─── READ all patients ─────────────────────────────────────────
@csrf_exempt
def get_patients(request):
    try:
        from .patient_helpers import fetch_patients_list
        limit = request.GET.get("limit", 500)
        data = fetch_patients_list(limit=limit)
        return JsonResponse(data, safe=False)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def patients_poll_view(request):
    try:
        from .patient_helpers import patients_poll_token
        return JsonResponse(patients_poll_token())
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
# ─── UPDATE patient ────────────────────────────────────────────
@csrf_exempt
def update_patient(request, id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        patient = Patient.objects(id=id).first()
        if not patient:
            return JsonResponse({"error": "Patient not found"}, status=404)
 
        data  = json.loads(request.body)
        name  = data.get("name", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
 
        if not name or not email:
            return JsonResponse({"error": "Name and email are required"}, status=400)
 
        # Email uniqueness check (exclude self)
        existing = Patient.objects(email=email).first()
        if existing and str(existing.id) != id:
            return JsonResponse({"error": "Another patient already uses this email"}, status=400)
 
        patient.name  = name
        patient.email = email
        patient.phone = phone
        patient.save()
 
        return JsonResponse({"message": "Patient updated successfully"})
 
    except Exception as e:
        print(f"UPDATE PATIENT ERROR: {e}")
        return JsonResponse({"error": str(e)}, status=500)
 
 
# ─── DELETE patient ────────────────────────────────────────────
@csrf_exempt
def delete_patient(request, id):
    if request.method != "DELETE":
        return JsonResponse({"error": "Only DELETE allowed"}, status=405)
    try:
        patient = Patient.objects(id=id).first()
        if not patient:
            return JsonResponse({"error": "Patient not found"}, status=404)
 
        # Unlink from appointments so they don't become orphaned
        for appt in (patient.appointments or []):
            try:
                appt.patient = None
                appt.save()
            except Exception:
                pass
 
        patient.delete()
        return JsonResponse({"message": "Patient deleted successfully"})
 
    except Exception as e:
        print(f"DELETE PATIENT ERROR: {e}")
        return JsonResponse({"error": str(e)}, status=500)
 
 
# ══════════════════════════════════════════════════════════════════
#  FIXED update_appointment_status
#  Key fixes:
#   1. Patient.save() returns None in MongoEngine — must NOT chain
#   2. appointment_serial is used as the patient record's serial
#      (same ID carried forward, never regenerated)
#   3. Existing patient record matched by email — never duplicated
# ══════════════════════════════════════════════════════════════════
@csrf_exempt
def _send_appointment_email(appointment, status):
    """
    Send a beautifully formatted HTML email to the patient when an admin
    updates their appointment status (Approved / Cancelled / Delay).
    Falls back to plain-text if HTML rendering fails.
    """
    from django.core.mail import EmailMultiAlternatives

    patient_name = appointment.patient_name or "Valued Patient"
    patient_email = appointment.patient_email
    if not patient_email:
        return

    service_name = appointment.service_name or "Dental Consultation"
    try:
        import pytz as _pytz
        _PKT = _pytz.timezone("Asia/Karachi")
        _dt = appointment.date
        if _dt.tzinfo is None:
            _dt = _pytz.utc.localize(_dt)
        date_str = _dt.astimezone(_PKT).strftime("%A, %d %B %Y at %I:%M %p")
    except Exception:
        date_str = "your scheduled time"

    FROM_EMAIL = "DentisTree Dental Clinic <rababzahra425@gmail.com>"
    CLINIC_NAME = "DentisTree Dental Clinic"
    CLINIC_PHONE = "+92-XXX-XXXXXXX"   # update with real number
    CLINIC_ADDRESS = "DentisTree Dental Clinic, Pakistan"

    # ── Shared HTML wrapper ────────────────────────────────────────────
    def _wrap(accent_color, icon, subject_line, body_html):
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

        <!-- Header band -->
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

        <!-- Status badge -->
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

        <!-- Body -->
        <tr>
          <td style="padding:24px 40px 32px;">
            <p style="margin:0 0 18px;font-size:15px;color:#1e293b;">
              Dear <strong>{patient_name}</strong>,
            </p>
            {body_html}

            <!-- Appointment detail card -->
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
              <a href="tel:{CLINIC_PHONE}" style="color:#0d9488;text-decoration:none;">
                {CLINIC_PHONE}
              </a>.
            </p>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#f8fafc;border-top:1px solid #e2e8f0;
                     padding:20px 40px;text-align:center;">
            <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;">
              {CLINIC_ADDRESS}<br/>
              <a href="mailto:{FROM_EMAIL}"
                 style="color:#0d9488;text-decoration:none;">{FROM_EMAIL}</a>
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

    # ── Per-status content ─────────────────────────────────────────────
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
        html = _wrap("#0d9488", "✅", "Appointment Confirmed", body_html)

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
        html = _wrap("#dc2626", "❌", "Appointment Not Approved", body_html)

    elif status == "Delay":
        subject = f"Appointment Rescheduling Notice — {CLINIC_NAME}"
        plain = (
            f"Dear {patient_name},\n\n"
            f"We would like to inform you that your appointment for {service_name} "
            f"on {date_str} has been temporarily delayed.\n\n"
            f"Please be assured that your appointment has NOT been cancelled. "
            f"A member of our team will contact you shortly to coordinate a new "
            f"time that is convenient for you.\n\n"
            f"We apologise for the inconvenience and appreciate your patience.\n\n"
            f"Warm regards,\n{CLINIC_NAME}"
        )
        body_html = f"""
            <p style="font-size:15px;color:#1e293b;line-height:1.7;margin:0 0 14px;">
              We would like to inform you that your upcoming appointment has been
              <strong style="color:#d97706;">temporarily delayed</strong>.
            </p>
            <p style="font-size:15px;color:#1e293b;line-height:1.7;margin:0 0 14px;">
              Please be assured that your appointment has
              <strong>not been cancelled</strong>. This is only a temporary delay
              due to unforeseen circumstances at our end.
            </p>
            <p style="font-size:15px;color:#1e293b;line-height:1.7;margin:0;">
              A member of our dedicated team will reach out to you
              <strong>very shortly</strong> to coordinate a new time that is
              perfectly convenient for you. We truly appreciate your patience
              and understanding.
            </p>"""
        html = _wrap("#d97706", "⏳", "Appointment Delayed", body_html)

    else:
        return  # unknown status — do nothing

    # ── Send ──────────────────────────────────────────────────────────
    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain,
        from_email=FROM_EMAIL,
        to=[patient_email],
    )
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=False)


@csrf_exempt
def update_appointment_status(request, id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
 
    try:
        data   = json.loads(request.body)
        status = data.get("status")
 
        if status not in ["Approved", "Cancelled", "Delay"]:
            return JsonResponse({"error": "Invalid status value"}, status=400)
 
        appointment = Appointment.objects(id=id).first()
        if not appointment:
            return JsonResponse({"error": "Appointment not found"}, status=404)
 
        if appointment.status != "Pending":
            return JsonResponse({"error": "This appointment has already been processed."}, status=400)
 
        appointment.status = status
        appointment.save()
 
        # ── Auto-create / link Patient when Approved ──────────
        if status == "Approved":
            patient = Patient.objects(email=appointment.patient_email).first()
 
            if not patient:
                # FIX: use appointment_serial as the patient serial so
                # "the same ID carries forward" as required.
                new_serial = appointment.appointment_serial or 1
 
                # Build and save separately (MongoEngine .save() returns None)
                patient = Patient(
                    name=appointment.patient_name,
                    email=appointment.patient_email,
                    phone=appointment.patient_phone,
                    patient_serial=new_serial,
                    appointments=[appointment],
                )
                patient.save()          # ← correct: save on object, not chained
 
            else:
                # Existing patient — append appointment if not already linked
                linked_ids = [str(a.id) for a in (patient.appointments or [])]
                if str(appointment.id) not in linked_ids:
                    patient.appointments.append(appointment)
                    patient.save()
 
            # Link back to appointment
            if not appointment.patient:
                appointment.patient = patient
                appointment.save()
 
        # ── Email notification ─────────────────────────────────
        if appointment.patient_email:
            try:
                from django.core.mail import EmailMultiAlternatives
                _send_appointment_email(appointment, status)
            except Exception as mail_err:
                print(f"EMAIL ERROR: {mail_err}")
 
        return JsonResponse({"message": "Status updated successfully!"})
 
    except Exception as e:
        print(f"STATUS UPDATE ERROR: {e}")
        return JsonResponse({"error": str(e)}, status=500)
 
    
# import os
# from django.conf import settings
# from .models import BeforeAfterImage
 
# @csrf_exempt
# def create_before_after(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "Only POST allowed"}, status=405)
#     try:
#         service_id = request.POST.get("service_id")
#         description = request.POST.get("description", "")
#         before_file = request.FILES.get("before_image")
#         after_file = request.FILES.get("after_image")
 
#         if not service_id:
#             return JsonResponse({"error": "service_id is required"}, status=400)
#         if not before_file or not after_file:
#             return JsonResponse({"error": "Both before_image and after_image are required"}, status=400)
 
#         service = Service.objects(id=service_id).first()
#         if not service:
#             return JsonResponse({"error": "Service not found"}, status=404)
 
#         # Save files to MEDIA_ROOT/before_after/
#         upload_dir = os.path.join(settings.MEDIA_ROOT, "before_after")
#         os.makedirs(upload_dir, exist_ok=True)
 
#         before_filename = f"before_{before_file.name}"
#         after_filename = f"after_{after_file.name}"
 
#         before_path = os.path.join(upload_dir, before_filename)
#         after_path = os.path.join(upload_dir, after_filename)
 
#         with open(before_path, "wb") as f:
#             for chunk in before_file.chunks():
#                 f.write(chunk)
 
#         with open(after_path, "wb") as f:
#             for chunk in after_file.chunks():
#                 f.write(chunk)
 
#         # Store relative path in DB
#         image = BeforeAfterImage(
#             service=service,
#             before_image=f"before_after/{before_filename}",
#             after_image=f"before_after/{after_filename}",
#             description=description
#         ).save()
 
#         return JsonResponse({"message": "Image pair created successfully", "id": str(image.id)}, status=201)
 
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)
 
 
# def get_before_after_images(request):
#     try:
#         items = BeforeAfterImage.objects()
#         data = []
#         for item in items:
#             try:
#                 service_name = item.service.name
#                 service_id = str(item.service.id)
#             except:
#                 service_name = None
#                 service_id = None
 
#             data.append({
#                 "id": str(item.id),
#                 "service_name": service_name,
#                 "service_id": service_id,
#                 "description": item.description,
#                 # Build full URL so React can display the image
#                 "before_image_url": f"{settings.MEDIA_URL}{item.before_image}",
#                 "after_image_url": f"{settings.MEDIA_URL}{item.after_image}",
#                 "created_at": str(item.created_at),
#             })
 
#         return JsonResponse(data, safe=False)
 
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)
 
 
# @csrf_exempt
# def update_before_after_image(request, id):
#     if request.method != "POST":
#         return JsonResponse({"error": "Only POST allowed"}, status=405)
#     try:
#         item = BeforeAfterImage.objects(id=id).first()
#         if not item:
#             return JsonResponse({"error": "Image pair not found"}, status=404)
 
#         service_id = request.POST.get("service_id")
#         description = request.POST.get("description")
#         before_file = request.FILES.get("before_image")
#         after_file = request.FILES.get("after_image")
 
#         if service_id:
#             service = Service.objects(id=service_id).first()
#             if service:
#                 item.service = service
 
#         if description is not None:
#             item.description = description
 
#         upload_dir = os.path.join(settings.MEDIA_ROOT, "before_after")
#         os.makedirs(upload_dir, exist_ok=True)
 
#         # Only replace image if a new file was uploaded
#         if before_file:
#             before_filename = f"before_{before_file.name}"
#             before_path = os.path.join(upload_dir, before_filename)
#             with open(before_path, "wb") as f:
#                 for chunk in before_file.chunks():
#                     f.write(chunk)
#             item.before_image = f"before_after/{before_filename}"
 
#         if after_file:
#             after_filename = f"after_{after_file.name}"
#             after_path = os.path.join(upload_dir, after_filename)
#             with open(after_path, "wb") as f:
#                 for chunk in after_file.chunks():
#                     f.write(chunk)
#             item.after_image = f"before_after/{after_filename}"
 
#         item.save()
#         return JsonResponse({"message": "Image pair updated successfully"})
 
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)
 
 
# @csrf_exempt
# def delete_before_after_image(request, id):
#     if request.method != "POST":
#         return JsonResponse({"error": "Only POST allowed"}, status=405)
#     try:
#         item = BeforeAfterImage.objects(id=id).first()
#         if not item:
#             return JsonResponse({"error": "Image pair not found"}, status=404)
 
#         # Optionally delete physical files too
#         for path_field in [item.before_image, item.after_image]:
#             try:
#                 full_path = os.path.join(settings.MEDIA_ROOT, path_field)
#                 if os.path.exists(full_path):
#                     os.remove(full_path)
#             except:
#                 pass
 
#         item.delete()
#         return JsonResponse({"message": "Deleted successfully"})
 
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)
 


 # =======================
# REVIEWS (Updated)
# =======================
# Replace your existing create_review and get_reviews with these 3 functions
# Also make sure models.py Review model has customer_name field (see updated models.py)
 
# @csrf_exempt
# def create_review(request):
#     """
#     Called from the CUSTOMER website form.
#     Body: { customer_name, customer_email (optional), service_id (optional), rating, comment }
#     """
#     if request.method != "POST":
#         return JsonResponse({"error": "Only POST allowed"}, status=405)
#     try:
#         data = json.loads(request.body)
 
#         rating = data.get("rating")
#         if not rating:
#             return JsonResponse({"error": "rating is required"}, status=400)
 
#         customer_name = data.get("customer_name", "Anonymous")
#         if not customer_name or not customer_name.strip():
#             customer_name = "Anonymous"
 
#         # Optional: link to a service
#         service_id = data.get("service_id")
#         service_obj = None
#         if service_id:
#             service_obj = Service.objects(id=service_id).first()
 
#         review = Review(
#             customer_name=customer_name.strip(),
#             customer_email=data.get("customer_email", ""),
#             service=service_obj,
#             rating=int(rating),
#             comment=data.get("comment", ""),
#         ).save()
 
#         return JsonResponse({"message": "Review submitted successfully", "id": str(review.id)}, status=201)
 
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)
 
 
# def get_reviews(request):
#     """
#     Called by admin panel to display all reviews.
#     Supports optional ?rating=4 filter query param.
#     """
#     try:
#         rating_filter = request.GET.get("rating")
 
#         if rating_filter:
#             reviews = Review.objects(rating=int(rating_filter))
#         else:
#             reviews = Review.objects()
 
#         # Sort newest first
#         reviews = reviews.order_by("-created_at")
 
#         data = []
#         for r in reviews:
#             # Safe service dereference
#             try:
#                 service_name = r.service.name if r.service else None
#                 service_id = str(r.service.id) if r.service else None
#             except:
#                 service_name = None
#                 service_id = None
 
#             data.append({
#                 "id": str(r.id),
#                 "customer_name": r.customer_name or "Anonymous",
#                 "customer_email": r.customer_email or "",
#                 "service_name": service_name,
#                 "service_id": service_id,
#                 "rating": r.rating,
#                 "comment": r.comment or "",
#                 "created_at": r.created_at.strftime("%b %d, %Y") if r.created_at else "",
#             })
 
#         return JsonResponse(data, safe=False)
 
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)
 
@csrf_exempt
def create_review(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        data = json.loads(request.body)
 
        rating = data.get("rating")
        if not rating:
            return JsonResponse({"error": "rating is required"}, status=400)
 
        customer_name = data.get("customer_name", "Anonymous").strip() or "Anonymous"
 
        # Sirf zaroori details save ho rahi hain
        review = Review(
            customer_name=customer_name,
            rating=int(rating),
            comment=data.get("comment", ""),
        ).save()

        try:
            notify_new_review(customer_name, int(rating))
        except Exception:
            pass
 
        return JsonResponse({"message": "Review submitted successfully", "id": str(review.id)}, status=201)
 
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
def get_reviews(request):
    try:
        rating_filter = request.GET.get("rating")
 
        if rating_filter:
            reviews = Review.objects(rating=int(rating_filter))
        else:
            reviews = Review.objects()
 
        # Newest first
        reviews = reviews.order_by("-created_at")
 
        data = []
        for r in reviews:
            data.append({
                "id": str(r.id),
                "customer_name": r.customer_name or "Anonymous",
                "rating": r.rating,
                "comment": r.comment or "",
                "created_at": r.created_at.strftime("%b %d, %Y") if r.created_at else "",
            })
 
        return JsonResponse(data, safe=False)
 
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
@csrf_exempt
def delete_review(request, id):
    """Called from admin panel delete button."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        review = Review.objects(id=id).first()
        if not review:
            return JsonResponse({"error": "Review not found"}, status=404)
        review.delete()
        return JsonResponse({"message": "Review deleted successfully"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



# =======================
# EMPLOYEES
# =======================
# Add this to the bottom of your views.py
# Also add to your models.py import line:
#   from .models import ..., Employee
 
from .models import Employee
 
@csrf_exempt
def create_employee(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        data = json.loads(request.body)
 
        if not data.get("name"):
            return JsonResponse({"error": "name is required"}, status=400)
 
        employee = Employee(
            name=data.get("name"),
            father_name=data.get("father_name", ""),
            id_card_number=data.get("id_card_number", ""),
            designation=data.get("designation", ""),
            department=data.get("department", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            address=data.get("address", ""),
            salary=float(data.get("salary", 0)),
            join_date=data.get("join_date", ""),
            status=data.get("status", "Active"),
            salary_status=data.get("salary_status", "Unpaid"),
         )
        employee.save()

        return JsonResponse({"message": "Employee added successfully", "id": str(employee.id)}, status=201)
 
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
def get_employees(request):
    try:
        employees = Employee.objects().order_by("name")
        data = []
        for e in employees:
            data.append({
                "id": str(e.id),
                "name": e.name,
                "father_name": e.father_name or "",
                "id_card_number": e.id_card_number or "",
                "designation": e.designation or "",
                "department": e.department or "",
                "phone": e.phone or "",
                "email": e.email or "",
                "address": e.address or "",
                "salary": e.salary or 0,
                "join_date": e.join_date or "",
                "status": e.status or "Active",
                "salary_status": e.salary_status or "Unpaid",
            })
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
@csrf_exempt
def update_employee(request, id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        employee = Employee.objects(id=id).first()
        if not employee:
            return JsonResponse({"error": "Employee not found"}, status=404)
 
        data = json.loads(request.body)
 
        employee.name = data.get("name", employee.name)
        employee.father_name = data.get("father_name", employee.father_name)
        employee.id_card_number = data.get("id_card_number", employee.id_card_number)
        employee.designation = data.get("designation", employee.designation)
        employee.department = data.get("department", employee.department)
        employee.phone = data.get("phone", employee.phone)
        employee.email = data.get("email", employee.email)
        employee.address = data.get("address", employee.address)
        employee.salary = float(data.get("salary", employee.salary or 0))
        employee.join_date = data.get("join_date", employee.join_date)
        employee.status = data.get("status", employee.status)
        employee.salary_status = data.get("salary_status", employee.salary_status or "Unpaid")
        
        employee.save()
 
        return JsonResponse({"message": "Employee updated successfully"})
 
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
@csrf_exempt
def delete_employee(request, id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        employee = Employee.objects(id=id).first()
        if not employee:
            return JsonResponse({"error": "Employee not found"}, status=404)
        employee.delete()
        return JsonResponse({"message": "Employee deleted successfully"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def update_salary_status(request, id):
    """Toggle or set salary_status for a single employee."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        employee = Employee.objects(id=id).first()
        if not employee:
            return JsonResponse({"error": "Employee not found"}, status=404)

        data = json.loads(request.body)
        new_status = data.get("salary_status")

        if new_status not in ("Paid", "Unpaid"):
            return JsonResponse({"error": "salary_status must be 'Paid' or 'Unpaid'"}, status=400)

        employee.salary_status = new_status
        employee.save()
        return JsonResponse({"message": f"Salary status updated to {new_status}", "salary_status": new_status})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def reset_all_salary_status(request):
    """
    Manually reset ALL employees' salary_status to 'Unpaid'.
    Also used internally by the monthly auto-reset scheduler.
    POST /employees/salary/reset-all/
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        updated = Employee.objects().update(salary_status="Unpaid")
        return JsonResponse({
            "message": f"Salary status reset to Unpaid for {updated} employee(s).",
            "updated": updated,
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# =======================
# SUPPLIERS
# =======================

from .models import Supplier, InventoryItem
 
@csrf_exempt
def create_supplier(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        data = json.loads(request.body)
        if not data.get("name"):
            return JsonResponse({"error": "Supplier name is required"}, status=400)
        supplier = Supplier(
            name=data.get("name"),
            contact_person=data.get("contact_person", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            address=data.get("address", ""),
        )
        supplier.save()
        return JsonResponse({"message": "Supplier added", "id": str(supplier.id)}, status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
def get_suppliers(request):
    try:
        suppliers = Supplier.objects().order_by("name")
        data = []
        for s in suppliers:
            data.append({
                "id": str(s.id),
                "name": s.name,
                "contact_person": s.contact_person or "",
                "phone": s.phone or "",
                "email": s.email or "",
                "address": s.address or "",
            })
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
@csrf_exempt
def update_supplier(request, id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        supplier = Supplier.objects(id=id).first()
        if not supplier:
            return JsonResponse({"error": "Supplier not found"}, status=404)
        data = json.loads(request.body)
        supplier.name = data.get("name", supplier.name)
        supplier.contact_person = data.get("contact_person", supplier.contact_person)
        supplier.phone = data.get("phone", supplier.phone)
        supplier.email = data.get("email", supplier.email)
        supplier.address = data.get("address", supplier.address)
        supplier.save()
        return JsonResponse({"message": "Supplier updated"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
@csrf_exempt
def delete_supplier(request, id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        supplier = Supplier.objects(id=id).first()
        if not supplier:
            return JsonResponse({"error": "Supplier not found"}, status=404)
        supplier.delete()
        return JsonResponse({"message": "Supplier deleted"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
# =======================
# INVENTORY
# =======================
 
@csrf_exempt
def create_inventory_item(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        data = json.loads(request.body)
        if not data.get("name"):
            return JsonResponse({"error": "Item name is required"}, status=400)
        if not data.get("category"):
            return JsonResponse({"error": "Category is required"}, status=400)
 
        # Optional: link to Supplier document
        supplier_obj = None
        if data.get("supplier_id"):
            supplier_obj = Supplier.objects(id=data.get("supplier_id")).first()
 
        item = InventoryItem(
            name=data.get("name"),
            category=data.get("category"),
            quantity=float(data.get("quantity", 0)),
            unit=data.get("unit", "pieces"),
            cost_price=float(data.get("cost_price", 0)),
            supplier_name=data.get("supplier_name", ""),
            supplier=supplier_obj,
            expiry_date=data.get("expiry_date", ""),
            low_stock_threshold=float(data.get("low_stock_threshold", 10)),
        ).save()

        try:
            threshold = float(data.get("low_stock_threshold", 10))
            qty = float(data.get("quantity", 0))
            if qty <= threshold:
                notify_low_inventory(data.get("name", "Item"), qty, threshold)
        except Exception:
            pass

        try:
            threshold = float(data.get("low_stock_threshold", 10))
            qty = float(data.get("quantity", 0))
            if qty <= threshold:
                _create_low_stock_notification(
                data.get("name", "Item"), qty,
                data.get("unit", "pieces"), threshold,
                item_id=item.id
        )
        except Exception:
            pass
 
        return JsonResponse({"message": "Item added", "id": str(item.id)}, status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
def get_inventory(request):
    try:
        category_filter = request.GET.get("category")
        if category_filter and category_filter != "All":
            items = InventoryItem.objects(category=category_filter)
        else:
            items = InventoryItem.objects()
 
        items = items.order_by("name")
 
        data = []
        for item in items:
            # Expiry status
            expiry_status = "ok"
            if item.expiry_date:
                try:
                    exp = datetime.strptime(item.expiry_date, "%Y-%m-%d").date()
                    today = datetime.date.today()
                    days_left = (exp - today).days
                    if days_left < 0:
                        expiry_status = "expired"
                    elif days_left <= 7:
                        expiry_status = "near"
                except:
                    expiry_status = "ok"
 
            # Stock status
            stock_status = "ok"
            if item.quantity <= 0:
                stock_status = "out"
            elif item.quantity <= (item.low_stock_threshold or 10):
                stock_status = "low"
 
            # Supplier name
            supplier_name = item.supplier_name or ""
            if not supplier_name and item.supplier:
                try:
                    supplier_name = item.supplier.name
                except:
                    supplier_name = ""
 
            data.append({
                "id": str(item.id),
                "name": item.name,
                "category": item.category,
                "quantity": item.quantity,
                "unit": item.unit or "pieces",
                "cost_price": item.cost_price or 0,
                "supplier_name": supplier_name,
                "expiry_date": item.expiry_date or "",
                "low_stock_threshold": item.low_stock_threshold or 10,
                "stock_status": stock_status,
                "expiry_status": expiry_status,
            })
 
        return JsonResponse(data, safe=False)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)
 
 
@csrf_exempt
def update_inventory_item(request, id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        item = InventoryItem.objects(id=id).first()
        if not item:
            return JsonResponse({"error": "Item not found"}, status=404)
        data = json.loads(request.body)
 
        item.name = data.get("name", item.name)
        item.category = data.get("category", item.category)
        item.quantity = float(data.get("quantity", item.quantity))
        item.unit = data.get("unit", item.unit)
        item.cost_price = float(data.get("cost_price", item.cost_price or 0))
        item.supplier_name = data.get("supplier_name", item.supplier_name)
        item.expiry_date = data.get("expiry_date", item.expiry_date)
        item.low_stock_threshold = float(data.get("low_stock_threshold", item.low_stock_threshold or 10))
        item.updated_at = datetime.utcnow()
        item.save()

        # try:
        #     threshold = item.low_stock_threshold or 10
        #     if item.quantity <= threshold:
        #         notify_low_inventory(item.name, item.quantity, threshold)
        # except Exception:
        #     pass

        # try:
        #     threshold = item.low_stock_threshold or 10
        #     if item.quantity <= threshold:
        #         notify_low_inventory(item.name, item.quantity, threshold) 
        # except Exception:
        #     pass

        # try:
        #     threshold = item.low_stock_threshold or 10
        #     if item.quantity <= threshold:
        #         _create_low_stock_notification(
        #     item.name, item.quantity,
        #     item.unit, threshold
        # )
        # except Exception:
        #     pass
        try:
            threshold = item.low_stock_threshold or 10
            if item.quantity <= threshold:
                _create_low_stock_notification(
                item.name, item.quantity,
                item.unit, threshold,
                item_id=item.id      # ← this is what makes the notification link to the row
        )
        except Exception:
            pass
 
        return JsonResponse({"message": "Item updated"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
@csrf_exempt
def adjust_stock(request, id):
    """
    Add or reduce stock.
    Body: { "action": "add" | "reduce", "amount": 10 }
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        item = InventoryItem.objects(id=id).first()
        if not item:
            return JsonResponse({"error": "Item not found"}, status=404)
 
        data = json.loads(request.body)
        action = data.get("action")
        amount = float(data.get("amount", 0))
 
        if amount <= 0:
            return JsonResponse({"error": "Amount must be greater than 0"}, status=400)
 
        if action == "add":
            item.quantity += amount
        elif action == "reduce":
            if item.quantity < amount:
                return JsonResponse({"error": "Not enough stock to reduce"}, status=400)
            item.quantity -= amount
        else:
            return JsonResponse({"error": "action must be 'add' or 'reduce'"}, status=400)
 
        item.updated_at = datetime.utcnow()
        item.save()

# ADD THIS — stock reduction is the most common low-stock trigger
        try:
            threshold = item.low_stock_threshold or 10
            if item.quantity <= threshold:
                _create_low_stock_notification(
                    item.name, item.quantity,
                    item.unit, threshold,
                    item_id=item.id
        )
        except Exception:
            pass
 
        return JsonResponse({
            "message": f"Stock {'added' if action == 'add' else 'reduced'} successfully",
            "new_quantity": item.quantity
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
@csrf_exempt
def delete_inventory_item(request, id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        item = InventoryItem.objects(id=id).first()
        if not item:
            return JsonResponse({"error": "Item not found"}, status=404)
        item.delete()
        return JsonResponse({"message": "Item deleted"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# =======================
# FINANCIAL REPORT (replace existing financial_report view in views.py)
# Make sure these are in your imports: Employee, InventoryItem, Expense, Payment
# =======================
 
def financial_report(request):
    try:
        today = datetime.utcnow()
 
        def get_month_data(year, month):
            start = datetime(year, month, 1)
            end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
            month_str = f"{year}-{str(month).zfill(2)}"
            label = start.strftime("%b %Y")
 
            paid = Payment.objects(status="Paid", created_at__gte=start, created_at__lt=end)
            income = sum(float(p.amount or 0) for p in paid)
 
            manual_exps = Expense.objects(month=month_str)
            manual_total = sum(float(e.amount or 0) for e in manual_exps)
 
            salary_total = sum(float(e.salary or 0) for e in Employee.objects(status="Active"))
 
            inventory_total = sum(
                float(i.cost_price or 0) * float(i.quantity or 0)
                for i in InventoryItem.objects()
            )
 
            total_expenses = manual_total + salary_total + inventory_total
            net_profit = income - total_expenses
 
            cat_breakdown = {
                "Salary": round(salary_total, 2),
                "Inventory": round(inventory_total, 2),
            }
            for e in manual_exps:
                cat_breakdown[e.category] = round(
                    cat_breakdown.get(e.category, 0) + float(e.amount or 0), 2
                )
 
            return {
                "month": month_str,
                "label": label,
                "income": round(income, 2),
                "expenses": round(total_expenses, 2),
                "net_profit": round(net_profit, 2),
                "cat_breakdown": cat_breakdown,
            }
 
        months_data = []
        for i in range(5, -1, -1):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            months_data.append(get_month_data(y, m))
 
        current = months_data[-1]
        best = max(months_data, key=lambda x: x["net_profit"])
        cat_breakdown = current["cat_breakdown"]
 
        return JsonResponse({
            "current_month": current["label"],
            "summary": {
                "total_income": current["income"],
                "total_expenses": current["expenses"],
                "net_p899rofit": current["net_profit"],
                "best_month": best["label"],
                "best_month_profit": best["net_profit"],
            },
            "bar_chart": {
                "labels":   [m["label"]    for m in months_data],
                "income":   [m["income"]   for m in months_data],
                "expenses": [m["expenses"] for m in months_data],
            },
            "line_chart": {
                "labels": [m["label"]      for m in months_data],
                "profit": [m["net_profit"] for m in months_data],
            },
            "donut_chart": {
                "labels": list(cat_breakdown.keys()),
                "values": list(cat_breakdown.values()),
            },
            "months_data": months_data,
        })
 
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
# =======================
# EXPENSES
# =======================
# Add to top imports:
# from .models import ..., Expense
 
# from .models import Expense
 
# @csrf_exempt
# def create_expense(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "Only POST allowed"}, status=405)
#     try:
#         data = json.loads(request.body)
#         if not data.get("title"):
#             return JsonResponse({"error": "title is required"}, status=400)
#         if not data.get("category"):
#             return JsonResponse({"error": "category is required"}, status=400)
#         if not data.get("amount"):
#             return JsonResponse({"error": "amount is required"}, status=400)
 
#         # Default month to current if not provided
#         month = data.get("month") or datetime.utcnow().strftime("%Y-%m")
 
#         expense = Expense(
#             title=data.get("title"),
#             category=data.get("category"),
#             amount=float(data.get("amount")),
#             month=month,
#             note=data.get("note", ""),
#         ).save()
 
#         return JsonResponse({"message": "Expense added", "id": str(expense.id)}, status=201)
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)
 
 
# def get_expenses(request):
#     try:
#         month_filter = request.GET.get("month")  # e.g. ?month=2026-03
 
#         if month_filter:
#             expenses = Expense.objects(month=month_filter)
#         else:
#             expenses = Expense.objects()
 
#         expenses = expenses.order_by("-created_at")
 
#         data = []
#         for e in expenses:
#             data.append({
#                 "id": str(e.id),
#                 "title": e.title,
#                 "category": e.category,
#                 "amount": e.amount,
#                 "month": e.month or "",
#                 "note": e.note or "",
#                 "created_at": e.created_at.strftime("%b %d, %Y") if e.created_at else "",
#             })
 
#         return JsonResponse(data, safe=False)
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)
 
 
# @csrf_exempt
# def update_expense(request, id):
#     if request.method != "POST":
#         return JsonResponse({"error": "Only POST allowed"}, status=405)
#     try:
#         expense = Expense.objects(id=id).first()
#         if not expense:
#             return JsonResponse({"error": "Expense not found"}, status=404)
#         data = json.loads(request.body)
#         expense.title = data.get("title", expense.title)
#         expense.category = data.get("category", expense.category)
#         expense.amount = float(data.get("amount", expense.amount))
#         expense.month = data.get("month", expense.month)
#         expense.note = data.get("note", expense.note)
#         expense.save()
#         return JsonResponse({"message": "Expense updated"})
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)
 
 
# @csrf_exempt
# def delete_expense(request, id):
#     if request.method != "POST":
#         return JsonResponse({"error": "Only POST allowed"}, status=405)
#     try:
#         expense = Expense.objects(id=id).first()
#         if not expense:
#             return JsonResponse({"error": "Expense not found"}, status=404)
#         expense.delete()
#         return JsonResponse({"message": "Expense deleted"})
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)
 
 
# def get_financial_summary(request):
#     """
#     Returns full financial summary for a given month:
#     - Auto salary total from Employees
#     - Auto inventory cost from InventoryItem
#     - Manual expenses from Expense model
#     - Total income from Payments
#     - Net profit
#     """
#     try:
#         month = request.GET.get("month") or datetime.datetime.utcnow().strftime("%Y-%m")
 
#         # ── 1. Auto: Total salary from active employees ──────────────────
#         active_employees = Employee.objects(status="Active")
#         total_salary = sum(float(e.salary or 0) for e in active_employees)
 
#         salary_detail = []
#         for e in active_employees:
#             salary_detail.append({
#                 "name": e.name,
#                 "designation": e.designation or "",
#                 "salary": float(e.salary or 0),
#             })
 
#         # ── 2. Auto: Inventory total cost (quantity × cost_price) ────────
#         inventory_items = InventoryItem.objects()
#         total_inventory = sum(
#             float(i.cost_price or 0) * float(i.quantity or 0)
#             for i in inventory_items
#         )
 
#         inventory_detail = []
#         for i in inventory_items:
#             cost = float(i.cost_price or 0) * float(i.quantity or 0)
#             if cost > 0:
#                 inventory_detail.append({
#                     "name": i.name,
#                     "quantity": i.quantity,
#                     "unit": i.unit,
#                     "cost_price": float(i.cost_price or 0),
#                     "total": cost,
#                 })
 
#         # ── 3. Manual expenses for this month ────────────────────────────
#         manual_expenses = Expense.objects(month=month).order_by("-created_at")
#         manual_list = []
#         category_totals = {}
 
#         for e in manual_expenses:
#             manual_list.append({
#                 "id": str(e.id),
#                 "title": e.title,
#                 "category": e.category,
#                 "amount": e.amount,
#                 "note": e.note or "",
#                 "created_at": e.created_at.strftime("%b %d, %Y") if e.created_at else "",
#             })
#             category_totals[e.category] = category_totals.get(e.category, 0) + e.amount
 
#         total_manual = sum(e.amount for e in manual_expenses)
 
#         # Add auto categories to breakdown
#         category_totals["Salary"] = category_totals.get("Salary", 0) + total_salary
#         category_totals["Inventory"] = category_totals.get("Inventory", 0) + total_inventory
 
#         # ── 4. Income: Total paid payments for this month ─────────────────
#         year, mon = month.split("-")
#         start = datetime(int(year), int(mon), 1)
#         if int(mon) == 12:
#             end = datetime(int(year) + 1, 1, 1)
#         else:
#             end = datetime(int(year), int(mon) + 1, 1)
 
#         paid_payments = Payment.objects(
#             status="Paid",
#             created_at__gte=start,
#             created_at__lt=end
#         )
#         total_income = sum(float(p.amount or 0) for p in paid_payments)
 
#         # ── 5. Net profit ─────────────────────────────────────────────────
#         total_expenses = total_salary + total_inventory + total_manual
#         net_profit = total_income - total_expenses
 
#         return JsonResponse({
#             "month": month,
#             "total_income": round(total_income, 2),
#             "total_expenses": round(total_expenses, 2),
#             "net_profit": round(net_profit, 2),
#             "breakdown": {
#                 "salary": round(total_salary, 2),
#                 "inventory": round(total_inventory, 2),
#                 "manual": round(total_manual, 2),
#                 "by_category": {k: round(v, 2) for k, v in category_totals.items()},
#             },
#             "salary_detail": salary_detail,
#             "inventory_detail": inventory_detail,
#             "manual_expenses": manual_list,
#         })
 
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)


# # =======================
# # FINANCIAL REPORT (replace existing financial_report view in views.py)
# # Make sure these are in your imports: Employee, InventoryItem, Expense, Payment
# # =======================

# def financial_report(request):
#     try:
#         today = datetime.utcnow()

#         def get_month_data(year, month):
#             start = datetime(year, month, 1)
#             end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
#             month_str = f"{year}-{str(month).zfill(2)}"
#             label = start.strftime("%b %Y")

#             paid = Payment.objects(status="Paid", created_at__gte=start, created_at__lt=end)
#             income = sum(float(p.amount or 0) for p in paid)

#             manual_exps = Expense.objects(month=month_str)
#             manual_total = sum(float(e.amount or 0) for e in manual_exps)

#             salary_total = sum(float(e.salary or 0) for e in Employee.objects(status="Active"))

#             inventory_total = sum(
#                 float(i.cost_price or 0) * float(i.quantity or 0)
#                 for i in InventoryItem.objects()
#             )

#             total_expenses = manual_total + salary_total + inventory_total
#             net_profit = income - total_expenses

#             cat_breakdown = {
#                 "Salary": round(salary_total, 2),
#                 "Inventory": round(inventory_total, 2),
#             }
#             for e in manual_exps:
#                 cat_breakdown[e.category] = round(
#                     cat_breakdown.get(e.category, 0) + float(e.amount or 0), 2
#                 )

#             return {
#                 "month": month_str,
#                 "label": label,
#                 "income": round(income, 2),
#                 "expenses": round(total_expenses, 2),
#                 "net_profit": round(net_profit, 2),
#                 "cat_breakdown": cat_breakdown,
#             }

#         months_data = []
#         for i in range(5, -1, -1):
#             m = today.month - i
#             y = today.year
#             while m <= 0:
#                 m += 12
#                 y -= 1
#             months_data.append(get_month_data(y, m))

#         current = months_data[-1]
#         best = max(months_data, key=lambda x: x["net_profit"])
#         cat_breakdown = current["cat_breakdown"]

#         return JsonResponse({
#             "current_month": current["label"],
#             "summary": {
#                 "total_income": current["income"],
#                 "total_expenses": current["expenses"],
#                 "net_profit": current["net_profit"],
#                 "best_month": best["label"],
#                 "best_month_profit": best["net_profit"],
#             },
#             "bar_chart": {
#                 "labels":   [m["label"]    for m in months_data],
#                 "income":   [m["income"]   for m in months_data],
#                 "expenses": [m["expenses"] for m in months_data],
#             },
#             "line_chart": {
#                 "labels": [m["label"]      for m in months_data],
#                 "profit": [m["net_profit"] for m in months_data],
#             },
#             "donut_chart": {
#                 "labels": list(cat_breakdown.keys()),
#                 "values": list(cat_breakdown.values()),
#             },
#             "months_data": months_data,
#         })

#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)

    
# =======================
# EXPENSES
# =======================
# Add to top imports:
# from .models import ..., Expense
 
from .models import Expense
 
@csrf_exempt
def create_expense(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        data = json.loads(request.body)
        if not data.get("title"):
            return JsonResponse({"error": "title is required"}, status=400)
        if not data.get("category"):
            return JsonResponse({"error": "category is required"}, status=400)
        if not data.get("amount"):
            return JsonResponse({"error": "amount is required"}, status=400)
 
        # Default month to current if not provided
        month = data.get("month") or datetime.utcnow().strftime("%Y-%m")
 
        expense = Expense(
            title=data.get("title"),
            category=data.get("category"),
            amount=float(data.get("amount")),
            month=month,
            note=data.get("note", ""),
        ).save()
 
        return JsonResponse({"message": "Expense added", "id": str(expense.id)}, status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
def get_expenses(request):
    try:
        month_filter = request.GET.get("month")  # e.g. ?month=2026-03
 
        if month_filter:
            expenses = Expense.objects(month=month_filter)
        else:
            expenses = Expense.objects()
 
        expenses = expenses.order_by("-created_at")
 
        data = []
        for e in expenses:
            data.append({
                "id": str(e.id),
                "title": e.title,
                "category": e.category,
                "amount": e.amount,
                "month": e.month or "",
                "note": e.note or "",
                "created_at": e.created_at.strftime("%b %d, %Y") if e.created_at else "",
            })
 
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
@csrf_exempt
def update_expense(request, id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        expense = Expense.objects(id=id).first()
        if not expense:
            return JsonResponse({"error": "Expense not found"}, status=404)
        data = json.loads(request.body)
        expense.title = data.get("title", expense.title)
        expense.category = data.get("category", expense.category)
        expense.amount = float(data.get("amount", expense.amount))
        expense.month = data.get("month", expense.month)
        expense.note = data.get("note", expense.note)
        expense.save()
        return JsonResponse({"message": "Expense updated"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
@csrf_exempt
def delete_expense(request, id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        expense = Expense.objects(id=id).first()
        if not expense:
            return JsonResponse({"error": "Expense not found"}, status=404)
        expense.delete()
        return JsonResponse({"message": "Expense deleted"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
def get_financial_summary(request):
    """
    Returns full financial summary for a given month:
    - Auto salary total from Employees
    - Auto inventory cost from InventoryItem
    - Manual expenses from Expense model
    - Total income from Payments
    - Net profit
    """
    try:
        month = request.GET.get("month") or datetime.utcnow().strftime("%Y-%m")
 
        # ── 1. Auto: Total salary — only employees with salary_status="Paid" ──
        active_employees = Employee.objects(status="Active")
        total_salary = sum(float(e.salary or 0) for e in active_employees if (e.salary_status or "Unpaid") == "Paid")
 
        salary_detail = []
        for e in active_employees:
            salary_detail.append({
                "name": e.name,
                "designation": e.designation or "",
                "salary": float(e.salary or 0),
                "salary_status": e.salary_status or "Unpaid",
            })
 
        # ── 2. Auto: Inventory total cost (quantity × cost_price) ────────
        inventory_items = InventoryItem.objects()
        total_inventory = sum(
            float(i.cost_price or 0) * float(i.quantity or 0)
            for i in inventory_items
        )
 
        inventory_detail = []
        for i in inventory_items:
            cost = float(i.cost_price or 0) * float(i.quantity or 0)
            if cost > 0:
                inventory_detail.append({
                    "name": i.name,
                    "quantity": i.quantity,
                    "unit": i.unit,
                    "cost_price": float(i.cost_price or 0),
                    "total": cost,
                })
 
        # ── 3. Manual expenses for this month ────────────────────────────
        manual_expenses = Expense.objects(month=month).order_by("-created_at")
        manual_list = []
        category_totals = {}
 
        for e in manual_expenses:
            manual_list.append({
                "id": str(e.id),
                "title": e.title,
                "category": e.category,
                "amount": e.amount,
                "note": e.note or "",
                "created_at": e.created_at.strftime("%b %d, %Y") if e.created_at else "",
            })
            category_totals[e.category] = category_totals.get(e.category, 0) + e.amount
 
        total_manual = sum(e.amount for e in manual_expenses)
 
        # Add auto categories to breakdown
        category_totals["Salary"] = category_totals.get("Salary", 0) + total_salary
        category_totals["Inventory"] = category_totals.get("Inventory", 0) + total_inventory
 
        # ── 4. Income: Total paid payments for this month ─────────────────
        year, mon = month.split("-")
        start = datetime(int(year), int(mon), 1)
        if int(mon) == 12:
            end = datetime(int(year) + 1, 1, 1)
        else:
            end = datetime(int(year), int(mon) + 1, 1)
 
        paid_payments = Payment.objects(
            status="Paid",
            created_at__gte=start,
            created_at__lt=end
        )
        total_income = sum(float(p.amount or 0) for p in paid_payments)
 
        # ── 5. Net profit ─────────────────────────────────────────────────
        total_expenses = total_salary + total_inventory + total_manual
        net_profit = total_income - total_expenses
 
        return JsonResponse({
            "month": month,
            "total_income": round(total_income, 2),
            "total_expenses": round(total_expenses, 2),
            "net_profit": round(net_profit, 2),
            "breakdown": {
                "salary": round(total_salary, 2),
                "inventory": round(total_inventory, 2),
                "manual": round(total_manual, 2),
                "by_category": {k: round(v, 2) for k, v in category_totals.items()},
            },
            "salary_detail": salary_detail,
            "inventory_detail": inventory_detail,
            "manual_expenses": manual_list,
        })
 
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# =======================
# FINANCIAL REPORT (replace existing financial_report view in views.py)
# Make sure these are in your imports: Employee, InventoryItem, Expense, Payment
# =======================

"""
FINANCIAL REPORT VIEW — add this to your views.py
Also add to urls.py:  path('reports/financial/', financial_report),

Imports needed at top of views.py (add if missing):
  from .models import Installment, Expense, Employee, InventoryItem
  from datetime import datetime, timedelta
  from collections import defaultdict
  import calendar
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Installment, Expense, Employee, InventoryItem
from collections import defaultdict
import calendar


def financial_report(request):
    """
    GET /reports/financial/?month=2026-05
    Returns a full financial summary for the given month (defaults to current month).
    """
    try:
        # ── 1. Resolve target month ───────────────────────────────
        month_param = request.GET.get("month", "")
        today = datetime.utcnow()

        if month_param:
            try:
                target = datetime.strptime(month_param, "%Y-%m")
            except ValueError:
                return JsonResponse({"error": "Invalid month format. Use YYYY-MM"}, status=400)
        else:
            target = today.replace(day=1)

        year  = target.year
        month = target.month

        # Month range
        _, last_day = calendar.monthrange(year, month)
        month_start = datetime(year, month, 1)
        month_end   = datetime(year, month, last_day, 23, 59, 59)

        # ── 2. Income: sum of Installment.amount this month ───────
        def get_income_for(y, m):
            _, ld = calendar.monthrange(y, m)
            ms = datetime(y, m, 1)
            me = datetime(y, m, ld, 23, 59, 59)
            total = 0.0
            for inst in Installment.objects(created_at__gte=ms, created_at__lte=me):
                total += inst.amount or 0
            return total

        # ── 3. Expenses: Salaries + Inventory cost + manual Expense docs ──
        def get_expenses_for(y, m):
            month_str = f"{y}-{str(m).zfill(2)}"
            _, ld = calendar.monthrange(y, m)
            ms = datetime(y, m, 1)
            me = datetime(y, m, ld, 23, 59, 59)

            # Active employee salaries
            salary_total = sum(
                (e.salary or 0)
                for e in Employee.objects(status="Active")
            )

            # Inventory cost (total cost of all items — represents capital tied up)
            inventory_total = sum(
                ((item.cost_price or 0) * (item.quantity or 0))
                for item in InventoryItem.objects()
            )

            # Manual expenses for this month
            manual_total = sum(
                (exp.amount or 0)
                for exp in Expense.objects(month=month_str)
                if exp.category not in ("Salary", "Inventory")  # avoid double-count
            )

            # Salary-category manual expenses (if admin added them separately)
            manual_salary = sum(
                (exp.amount or 0)
                for exp in Expense.objects(month=month_str, category="Salary")
            )

            # Use whichever salary is higher (avoids double count)
            final_salary = max(salary_total, manual_salary)

            return {
                "salary":    final_salary,
                "inventory": inventory_total,
                "other":     manual_total,
                "total":     final_salary + inventory_total + manual_total,
            }

        # ── 4. Build 6-month history ──────────────────────────────
        months_data = []
        for i in range(5, -1, -1):
            # Go back i months from target
            m_date = (target.replace(day=1) - timedelta(days=1)) if i > 0 else target
            # More reliable: subtract months properly
            total_months = year * 12 + month - 1 - i
            m_y = total_months // 12
            m_m = total_months % 12 + 1

            income   = get_income_for(m_y, m_m)
            exp_data = get_expenses_for(m_y, m_m)
            expenses = exp_data["total"]
            net      = income - expenses

            months_data.append({
                "label":      datetime(m_y, m_m, 1).strftime("%b %Y"),
                "month_key":  f"{m_y}-{str(m_m).zfill(2)}",
                "income":     round(income, 2),
                "expenses":   round(expenses, 2),
                "net_profit": round(net, 2),
            })

        # ── 5. Current month detail ───────────────────────────────
        cur_income   = get_income_for(year, month)
        cur_exp_data = get_expenses_for(year, month)
        cur_expenses = cur_exp_data["total"]
        cur_net      = cur_income - cur_expenses

        # ── 6. Summary ────────────────────────────────────────────
        best = max(months_data, key=lambda x: x["net_profit"])

        # ── 7. Chart data ─────────────────────────────────────────
        bar_labels  = [m["label"]      for m in months_data]
        bar_income  = [m["income"]     for m in months_data]
        bar_expenses= [m["expenses"]   for m in months_data]
        line_profit = [m["net_profit"] for m in months_data]

        # Donut: expense breakdown for current month
        donut_labels = []
        donut_values = []
        if cur_exp_data["salary"] > 0:
            donut_labels.append("Salary")
            donut_values.append(round(cur_exp_data["salary"], 2))
        if cur_exp_data["inventory"] > 0:
            donut_labels.append("Inventory")
            donut_values.append(round(cur_exp_data["inventory"], 2))
        if cur_exp_data["other"] > 0:
            donut_labels.append("Other Expenses")
            donut_values.append(round(cur_exp_data["other"], 2))

        # ── 8. Payment method breakdown ───────────────────────────
        method_counts = defaultdict(float)
        for inst in Installment.objects(created_at__gte=month_start, created_at__lte=month_end):
            method_counts[inst.method or "Cash"] += inst.amount or 0

        # ── 9. Manual expenses list for current month ─────────────
        month_str_cur = f"{year}-{str(month).zfill(2)}"
        manual_expenses = []
        for exp in Expense.objects(month=month_str_cur).order_by('-created_at'):
            manual_expenses.append({
                "id":       str(exp.id),
                "title":    exp.title,
                "category": exp.category,
                "amount":   exp.amount or 0,
                "note":     exp.note or "",
            })

        # ── 10. Active employees ──────────────────────────────────
        employees = []
        for e in Employee.objects(status="Active"):
            employees.append({
                "id":          str(e.id),
                "name":        e.name,
                "designation": e.designation or "",
                "salary":      e.salary or 0,
                "salary_status": e.salary_status or "Unpaid",
            })

        # ── 11. Inventory summary ─────────────────────────────────
        inventory_items = []
        for item in InventoryItem.objects():
            inventory_items.append({
                "id":         str(item.id),
                "name":       item.name,
                "category":   item.category,
                "quantity":   item.quantity or 0,
                "unit":       item.unit or "pieces",
                "cost_price": item.cost_price or 0,
                "total_cost": round((item.cost_price or 0) * (item.quantity or 0), 2),
            })

        return JsonResponse({
            "current_month": datetime(year, month, 1).strftime("%B %Y"),
            "month_key":     month_str_cur,
            "summary": {
                "total_income":      round(cur_income, 2),
                "total_expenses":    round(cur_expenses, 2),
                "net_profit":        round(cur_net, 2),
                "best_month":        best["label"],
                "best_month_profit": best["net_profit"],
            },
            "expense_breakdown": {
                "salary":    round(cur_exp_data["salary"], 2),
                "inventory": round(cur_exp_data["inventory"], 2),
                "other":     round(cur_exp_data["other"], 2),
            },
            "months_data": months_data,
            "bar_chart": {
                "labels":   bar_labels,
                "income":   bar_income,
                "expenses": bar_expenses,
            },
            "line_chart": {
                "labels": bar_labels,
                "profit": line_profit,
            },
            "donut_chart": {
                "labels": donut_labels,
                "values": donut_values,
            },
            "payment_methods": dict(method_counts),
            "manual_expenses": manual_expenses,
            "employees":       employees,
            "inventory_items": inventory_items,
            "active_employee_count": len(employees),
            "inventory_item_count":  len(inventory_items),
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({"error": str(e), "traceback": traceback.format_exc()}, status=500)

# =======================
# DASHBOARD
# =======================
import traceback


@csrf_exempt
def get_dashboard(request):
    try:
        from .dashboard_helpers import fetch_dashboard_data
        return JsonResponse(fetch_dashboard_data())
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e), "type": type(e).__name__}, status=500)


@csrf_exempt
def dashboard_poll_view(request):
    try:
        from .dashboard_helpers import dashboard_poll_token
        return JsonResponse(dashboard_poll_token())
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.views.decorators.http import require_GET
from django.middleware.csrf import get_token
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import base64


# ─── LOGIN ─────────────────────────────────────────
@csrf_exempt
@require_POST
def login_view(request):
    """
    Body: { "username": "...", "password": "..." }
    """

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return JsonResponse({"detail": "Username and password are required."}, status=400)

    user = authenticate(request, username=username, password=password)

    # Allow sign-in with email address as well as username
    if user is None and "@" in username:
        try:
            by_email = User.objects.get(email__iexact=username)
            user = authenticate(request, username=by_email.username, password=password)
        except User.DoesNotExist:
            pass

    if user is None:
        return JsonResponse({
            "detail": "Invalid username or password. Usernames are case-sensitive (usually 'admin').",
        }, status=401)

    if not user.is_active:
        return JsonResponse({"detail": "Account disabled"}, status=403)

    login(request, user)

    return JsonResponse({"user": _serialize_user(user)})


def _get_or_create_profile(user):
    """Get or create MongoDB UserProfile for a Django user (MongoEngine has no get_or_create)."""
    try:
        return UserProfile.objects.get(user_id=str(user.id))
    except UserProfile.DoesNotExist:
        profile = UserProfile(
            user_id=str(user.id),
            username=user.username,
            email=user.email or "",
            full_name=user.get_full_name() or user.username,
            is_superuser=user.is_superuser,
            is_staff=user.is_staff,
        )
        profile.save()
        return profile


def _serialize_user(user):
    """Build user dict for API responses, including Mongo UserProfile fields."""
    data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.get_full_name() or user.username,
        "is_superuser": user.is_superuser,
        "is_staff": user.is_staff,
        "phone": "",
        "clinic": "Dentistree Clinic",
        "role": "Super Admin" if user.is_superuser else "User",
        "photo": "",
    }
    try:
        profile = _get_or_create_profile(user)
        data["phone"] = profile.phone or ""
        data["clinic"] = profile.clinic or data["clinic"]
        data["role"] = profile.role or data["role"]
        data["photo"] = profile.photo or ""
        if profile.full_name:
            data["full_name"] = profile.full_name
    except Exception:
        pass
    return data


def _serialize_notifications(profile):
    """User-configurable notification types only."""
    return {
        "newAppointments": profile.notif_new_appointments,
        "reminders":       profile.notif_reminders,
        "reviews":         profile.notif_reviews,
        "inventory":       profile.notif_inventory,
        "reports":         profile.notif_reports,
    }


def _apply_notifications(profile, data):
    mapping = {
        "newAppointments": "notif_new_appointments",
        "reminders":       "notif_reminders",
        "reviews":         "notif_reviews",
        "inventory":       "notif_inventory",
        "reports":         "notif_reports",
    }
    for key, field in mapping.items():
        if key in data:
            setattr(profile, field, bool(data[key]))


@csrf_exempt
@require_GET
def csrf_token_view(request):
    """Set CSRF cookie for SPA clients (call before POST with credentials)."""
    get_token(request)
    return JsonResponse({"detail": "CSRF cookie set"})


@csrf_exempt
@require_GET
def auth_me_view(request):
    """Return current session user or 401."""
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Not authenticated"}, status=401)
    return JsonResponse({"user": _serialize_user(request.user)})


@csrf_exempt
def profile_view(request):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse({"detail": "Not authenticated"}, status=401)

    return JsonResponse({
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.get_full_name() or user.username,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
        }
    })


# @csrf_exempt
# @require_POST
# def update_profile_view(request):
#     user = request.user

#     if not user.is_authenticated:
#         return JsonResponse({"detail": "Authentication required"}, status=401)

#     try:
#         data = json.loads(request.body)
#     except json.JSONDecodeError:
#         return JsonResponse({"error": "Invalid JSON"}, status=400)

#     full_name = data.get("full_name", "")
#     email = data.get("email", "")
#     username = data.get("username", "")
#     phone = data.get("phone")
#     clinic = data.get("clinic")
#     role = data.get("role")

#     if full_name:
#         parts = full_name.split(" ", 1)
#         user.first_name = parts[0]
#         user.last_name = parts[1] if len(parts) > 1 else ""

#     if username:
#         if User.objects.filter(username=username).exclude(pk=user.pk).exists():
#             return JsonResponse({"error": "Username already taken"}, status=400)
#         user.username = username

#     if email:
#         user.email = email

#     user.save()

#     return JsonResponse({
#         "user": {
#             "id": user.id,
#             "username": user.username,
#             "email": user.email,
#             "full_name": user.get_full_name() or user.username,
#             "phone":user.phone,
#             "clinic":user.clinic,
#             "role":user.role,
            
#         }
#     })

# @csrf_exempt
# @require_POST
# def update_profile_view(request):
#     user = request.user

#     if not user.is_authenticated:
#         return JsonResponse({"detail": "Authentication required"}, status=401)

#     try:
#         data = json.loads(request.body)
#     except json.JSONDecodeError:
#         return JsonResponse({"error": "Invalid JSON"}, status=400)

#     full_name = data.get("full_name", "")
#     email = data.get("email", "")
#     username = data.get("username", "")
#     phone = data.get("phone", "")
#     clinic = data.get("clinic", "")
#     role = data.get("role", "")

#     # ── Django User update ─────────────────
#     if full_name:
#         parts = full_name.split(" ", 1)
#         user.first_name = parts[0]
#         user.last_name = parts[1] if len(parts) > 1 else ""

#     if username:
#         if User.objects.filter(username=username).exclude(pk=user.pk).exists():
#             return JsonResponse({"error": "Username already taken"}, status=400)

#         user.username = username

#     user.email = email
#     user.save()

#     # ── Mongo UserProfile update ───────────
#     profile, created = UserProfile.objects.get_or_create(
#         user_id=str(user.id)
#     )

#     profile.username = user.username
#     profile.email = user.email
#     profile.full_name = user.get_full_name()

#     profile.phone = phone
#     profile.clinic = clinic
#     profile.role = role

#     profile.is_superuser = user.is_superuser
#     profile.is_staff = user.is_staff

#     profile.save()

#     return JsonResponse({
#         "user": {
#             "id": user.id,
#             "username": profile.username,
#             "email": profile.email,
#             "full_name": profile.full_name,
#             "phone": profile.phone,
#             "clinic": profile.clinic,
#             "role": profile.role,
#             "is_superuser": profile.is_superuser,
#             "is_staff": profile.is_staff,
#         }
#     })
@csrf_exempt
@require_POST
def update_profile_view(request):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"detail": "Authentication required"}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    full_name = data.get("full_name", "")
    email = data.get("email", "")
    username = data.get("username", "")
    phone = data.get("phone", "")
    clinic = data.get("clinic", "")
    role = data.get("role", "")

    try:
        if full_name:
            parts = full_name.split(" ", 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ""

        if username:
            if User.objects.filter(username=username).exclude(pk=user.pk).exists():
                return JsonResponse({"error": "Username already taken"}, status=400)
            user.username = username

        user.email = email
        user.save()

        profile = _get_or_create_profile(user)
        profile.username = user.username
        profile.email = user.email or ""
        profile.full_name = full_name.strip() or user.get_full_name() or user.username
        profile.phone = phone
        profile.clinic = clinic
        profile.role = role
        profile.is_superuser = user.is_superuser
        profile.is_staff = user.is_staff

        if "photo" in data:
            photo_val = data.get("photo")
            profile.photo = "" if not photo_val else str(photo_val)

        profile.save()

        return JsonResponse({"user": _serialize_user(user)})

    except Exception as e:
        return JsonResponse({"error": f"Failed to save profile: {e}"}, status=500)

# Add this helper near the top of your notification section in views.py
# def _create_low_stock_notification(name, quantity, unit, threshold, item_id=None):
#     from datetime import datetime, timedelta
#     cooldown = datetime.utcnow() - timedelta(hours=24)
#     already = AdminNotification.objects(
#         notification_type="inventory",
#         title__icontains=name,
#         created_at__gte=cooldown,
#     ).first()
#     if not already:
#         AdminNotification(
#             notification_type="inventory",
#             title="Low Stock Alert",
#             message=f"{name} is low: {quantity} {unit or 'units'} (threshold: {threshold})",
#             link_page="inventory",           # ← navigates to inventory page
#             link_item_id=str(item_id) if item_id else "",  # ← highlights the row
#             is_read=False,
#         ).save()



# REPLACE the whole function with this:
def _create_low_stock_notification(name, quantity, unit, threshold, item_id=None):
    from datetime import datetime, timedelta
    cooldown = datetime.utcnow() - timedelta(hours=24)
    already = AdminNotification.objects(
        notification_type="inventory",
        title__icontains=name,
        created_at__gte=cooldown,
    ).first()
    if not already:
        AdminNotification(
            notification_type="inventory",
            title="Low Stock Alert",
            message=f"{name} is low: {quantity} {unit or 'units'} (threshold: {threshold})",
            link_page="inventory",
            link_item_id=str(item_id) if item_id else "",
            is_read=False,
        ).save()


@csrf_exempt
@require_GET
def get_notifications_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required"}, status=401)
    try:
        profile = _get_or_create_profile(request.user)
        return JsonResponse({"notifications": _serialize_notifications(profile)})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_POST
def update_notifications_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required"}, status=401)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        profile = _get_or_create_profile(request.user)
        prefs = data.get("notifications", data)
        _apply_notifications(profile, prefs)
        profile.save()
        return JsonResponse({
            "detail": "Notification preferences saved.",
            "notifications": _serialize_notifications(profile),
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_GET
def notification_feed_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required"}, status=401)
    try:
        from .notification_scheduler import (
            run_scheduled_notifications,
            enabled_notification_types_for_feed,
        )
        run_scheduled_notifications()
        limit = min(int(request.GET.get("limit", 40)), 100)
        enabled = enabled_notification_types_for_feed()
        qs = AdminNotification.objects(
            notification_type__in=list(enabled)
        ).order_by("-created_at")[:limit]
        items = [n.to_feed_dict() for n in qs]
        unread = AdminNotification.objects(
            notification_type__in=list(enabled), is_read=False
        ).count()
        return JsonResponse({"notifications": items, "unread_count": unread})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_GET
def notification_unread_count_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required"}, status=401)
    try:
        from .notification_scheduler import (
            run_scheduled_notifications,
            enabled_notification_types_for_feed,
        )
        run_scheduled_notifications()
        enabled = enabled_notification_types_for_feed()
        unread = AdminNotification.objects(
            notification_type__in=list(enabled), is_read=False
        ).count()
        return JsonResponse({"unread_count": unread})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_POST
def notification_mark_read_view(request, notif_id):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required"}, status=401)
    try:
        notif = AdminNotification.objects(id=notif_id).first()
        if not notif:
            return JsonResponse({"error": "Notification not found"}, status=404)
        notif.is_read = True
        notif.save()
        return JsonResponse({"detail": "Marked as read"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_POST
def notification_mark_all_read_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required"}, status=401)
    try:
        enabled = _enabled_notification_types()
        AdminNotification.objects(
            notification_type__in=list(enabled), is_read=False
        ).update(is_read=True)
        return JsonResponse({"detail": "All notifications marked as read"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    

def _check_and_notify_low_stock():
    from .models import InventoryItem, AdminNotification
    from datetime import datetime, timedelta

    cooldown = datetime.utcnow() - timedelta(hours=24)

    # FIX: query ALL items, then filter by threshold in Python
    for item in InventoryItem.objects():
        threshold = item.low_stock_threshold or 10
        if item.quantity <= threshold:
            already = AdminNotification.objects(
                notification_type="inventory",   # FIX: match the type used in TYPE_META
                title__icontains=item.name,
                created_at__gte=cooldown,
            ).first()
            if not already:
                AdminNotification(
                    notification_type="inventory",  # FIX: was "low_stock", not in TYPE_META
                    title="Low Stock Alert",
                    message=f"{item.name} is low: {item.quantity} {item.unit or 'units'} (threshold: {threshold})",
                    link_page="inventory",          # FIX: was missing — causes click to do nothing
                    is_read=False,
                ).save()


# views.py
@csrf_exempt
@require_POST
def notification_delete_view(request, notif_id):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required"}, status=401)
    try:
        notif = AdminNotification.objects(id=notif_id).first()
        if not notif:
            return JsonResponse({"error": "Notification not found"}, status=404)
        notif.delete()
        return JsonResponse({"detail": "Notification deleted"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# urls.py — add this line:

@csrf_exempt
@require_POST
def change_password_view(request):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse({"detail": "Authentication required"}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    current = data.get("current_password")
    new_pwd = data.get("new_password")
    confirm = data.get("confirm_password")

    if not user.check_password(current):
        return JsonResponse({"error": "Current password is wrong"}, status=400)

    if new_pwd != confirm:
        return JsonResponse({"error": "Passwords do not match"}, status=400)

    if len(new_pwd) < 8:
        return JsonResponse({"error": "Password too short"}, status=400)

    user.set_password(new_pwd)
    user.save()

    # Keep the user signed in after password change
    update_session_auth_hash(request, user)

    return JsonResponse({"detail": "Password changed successfully"})

# # LOGOUT
# def logout_view(request):
#     logout(request)
#     return JsonResponse({"message": "Logged out"})

@csrf_exempt
@require_GET
def check_auth(request):
    if request.user.is_authenticated:
        return JsonResponse({"authenticated": True, "user": _serialize_user(request.user)})
    return JsonResponse({"authenticated": False}, status=401)
    



import os
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import GalleryImage
# from services.models import Service  # adjust import to your project structure


# ─────────────────────────────────────────
# Helper: save uploaded file to disk
# ─────────────────────────────────────────
import os
import uuid
from django.conf import settings

def _save_upload(image_file, upload_dir):
    """Saves an uploaded file to the specified directory and returns the relative path."""
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
    
    # Generate a unique filename to avoid overwriting
    ext = os.path.splitext(image_file.name)[1]
    filename = f"{uuid.uuid4()}{ext}"
    full_path = os.path.join(upload_dir, filename)
    
    with open(full_path, 'wb+') as destination:
        for chunk in image_file.chunks():
            destination.write(chunk)
            
    # Return the path relative to MEDIA_ROOT (e.g., 'gallery/filename.jpg')
    return os.path.join("gallery", filename)



def _delete_file(rel_path):
    """Delete a media file if it exists; silently ignore errors."""
    try:
        full_path = os.path.join(settings.MEDIA_ROOT, rel_path)
        if os.path.exists(full_path):
            os.remove(full_path)
    except Exception:
        pass


def _image_url(rel_path):
    return f"{settings.MEDIA_URL}{rel_path}" if rel_path else None


# ─────────────────────────────────────────
# LIST  –  GET /gallery/
# ─────────────────────────────────────────
def list_gallery(request):
    """Return all records as a JSON array (for the index/table view)."""
    try:
        items = GalleryImage.objects()
        data = []
        for item in items:
            try:
                service_name = item.service.name
                service_id = str(item.service.id)
            except Exception:
                service_name = None
                service_id = None

            data.append({
                "id": str(item.id),
                "service_name": service_name,
                "service_id": service_id,
                "description": item.description,
                "image_url": _image_url(item.image),
                "video_url": _image_url(item.video),
                "created_at": str(item.created_at),
            })

        return JsonResponse(data, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ─────────────────────────────────────────
# DETAIL  –  GET /gallery/<id>/
# ─────────────────────────────────────────
def detail_gallery(request, id):
    """Return a single record (for the Show/View page)."""
    try:
        item = GalleryImage.objects(id=id).first()
        if not item:
            return JsonResponse({"error": "Record not found"}, status=404)

        try:
            service_name = item.service.name
            service_id = str(item.service.id)
        except Exception:
            service_name = None
            service_id = None

        return JsonResponse({
            "id": str(item.id),
            "service_name": service_name,
            "service_id": service_id,
            "description": item.description,
            "image_url": _image_url(item.image),
            "video_url": _image_url(item.video),
            "created_at": str(item.created_at),
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ─────────────────────────────────────────
# CREATE  –  POST /gallery/create/
# ─────────────────────────────────────────
@csrf_exempt
def create_gallery(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        service_id = request.POST.get("service_id")
        description = request.POST.get("description", "")
        image_file = request.FILES.get("image")
        video_file = request.FILES.get("video")

        if not service_id:
            return JsonResponse({"error": "service_id is required"}, status=400)
        if not image_file and not video_file:
            return JsonResponse({"error": "image is required"}, status=400)

        service = Service.objects(id=service_id).first()
        if not service:
            return JsonResponse({"error": "Service not found"}, status=404)

        upload_dir = os.path.join(settings.MEDIA_ROOT, "gallery")
        # rel_path = _save_upload(image_file, upload_dir)

        img_path = ""
        vid_path = ""

        if image_file:
            img_path = _save_upload(image_file,upload_dir)
        
        if video_file:
            vid_path = _save_upload(video_file, upload_dir)

        item = GalleryImage(
            service=service,
            image=img_path,
            video=vid_path,
            description=description,
        )
        item.save()

        return JsonResponse({
            "message": "Record created successfully",
            "id": str(item.id),
        }, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ─────────────────────────────────────────
# UPDATE  –  POST /gallery/update/<id>/
# ─────────────────────────────────────────
@csrf_exempt
def update_gallery(request, id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        item = GalleryImage.objects(id=id).first()
        if not item:
            return JsonResponse({"error": "Record not found"}, status=404)

        service_id = request.POST.get("service_id")
        description = request.POST.get("description")
        image_file = request.FILES.get("image")
        video_file = request.FILES.get("video")

        if service_id:
            service = Service.objects(id=service_id).first()
            if service:
                item.service = service

        if description is not None:
            item.description = description

        if image_file:
            # Remove old file first
            _delete_file(item.image)
            upload_dir = os.path.join(settings.MEDIA_ROOT, "gallery")
            item.image = _save_upload(image_file, upload_dir)
        
        
        if video_file:
            if hasattr(item,'video') and item.video:
                _delete_file(item.video)
            upload_dir = os.path.join(settings.MEDIA_ROOT, "gallery")
            item.video = _save_upload(video_file, upload_dir)

        item.save()
        return JsonResponse({"message": "Record updated successfully"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ─────────────────────────────────────────
# DELETE  –  POST /gallery/delete/<id>/
# ─────────────────────────────────────────
@csrf_exempt
def delete_gallery(request, id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        item = GalleryImage.objects(id=id).first()
        if not item:
            return JsonResponse({"error": "Record not found"}, status=404)

        _delete_file(item.image)

        if hasattr(item,'video') and item.video:
            _delete_file(item.video)


        item.delete()
        return JsonResponse({"message": "Deleted successfully"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    









# ─────────────────────────────────────────────────────────────
# ADD THESE VIEWS to your existing views.py
# Also import Prescription and TreatmentHistory at the top of views.py:
#   from .models import Prescription, TreatmentHistory
# ─────────────────────────────────────────────────────────────

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Prescription, TreatmentHistory, Patient, Appointment


# ═══════════════════════════════════════════════════════════════
# HELPER: serialize a Prescription document
# ═══════════════════════════════════════════════════════════════
def _serialize_rx(rx):
    try:
        patient_id = str(rx.patient.id) if rx.patient else None
    except Exception:
        patient_id = None

    try:
        appointment_id = str(rx.appointment.id) if rx.appointment else None
    except Exception:
        appointment_id = None

    return {
        "id":              str(rx.id),
        "patient_id":      patient_id,
        "appointment_id":  appointment_id,
        "medicines_text":  rx.medicines_text or "",
        "referred_by":     rx.referred_by    or "",
        "chief_complaint": rx.chief_complaint or "",
        "diagnosis":       rx.diagnosis      or "",
        "created_at":      rx.created_at.isoformat() if rx.created_at else None,
        "updated_at":      rx.updated_at.isoformat() if rx.updated_at else None,
    }


# ─────────────────────────────────────────
# LIST  –  GET /prescriptions/?patient_id=<id>
# ─────────────────────────────────────────
def list_prescriptions(request):
    patient_id = request.GET.get("patient_id")
    if not patient_id:
        return JsonResponse({"error": "patient_id is required"}, status=400)

    try:
        patient = Patient.objects(id=patient_id).first()
        if not patient:
            return JsonResponse({"error": "Patient not found"}, status=404)

        rxs = Prescription.objects(patient=patient)
        return JsonResponse([_serialize_rx(rx) for rx in rxs], safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ─────────────────────────────────────────
# CREATE  –  POST /prescriptions/create/
# ─────────────────────────────────────────
@csrf_exempt
def create_prescription(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)

        patient_id      = data.get("patient_id")
        appointment_id  = data.get("appointment_id")
        medicines_text  = data.get("medicines_text", "").strip()
        referred_by     = data.get("referred_by", "").strip()
        chief_complaint = data.get("chief_complaint", "").strip()
        diagnosis       = data.get("diagnosis", "").strip()

        if not patient_id:
            return JsonResponse({"error": "patient_id is required"}, status=400)
        if not medicines_text:
            return JsonResponse({"error": "medicines_text is required"}, status=400)

        patient = Patient.objects(id=patient_id).first()
        if not patient:
            return JsonResponse({"error": "Patient not found"}, status=404)

        appointment = None
        if appointment_id:
            appointment = Appointment.objects(id=appointment_id).first()

        rx = Prescription(
            patient         = patient,
            appointment     = appointment,
            medicines_text  = medicines_text,
            referred_by     = referred_by,
            chief_complaint = chief_complaint,
            diagnosis       = diagnosis,
        )
        rx.save()

        return JsonResponse({"message": "Prescription created", "id": str(rx.id)}, status=201)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ─────────────────────────────────────────
# UPDATE  –  POST /prescriptions/update/<id>/
# ─────────────────────────────────────────
@csrf_exempt
def update_prescription(request, id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        rx = Prescription.objects(id=id).first()
        if not rx:
            return JsonResponse({"error": "Prescription not found"}, status=404)

        data = json.loads(request.body)

        if "medicines_text" in data:
            medicines_text = data["medicines_text"].strip()
            if not medicines_text:
                return JsonResponse({"error": "medicines_text cannot be empty"}, status=400)
            rx.medicines_text = medicines_text

        if "referred_by"     in data: rx.referred_by     = data["referred_by"].strip()
        if "chief_complaint" in data: rx.chief_complaint = data["chief_complaint"].strip()
        if "diagnosis"       in data: rx.diagnosis       = data["diagnosis"].strip()

        if "appointment_id" in data and data["appointment_id"]:
            appt = Appointment.objects(id=data["appointment_id"]).first()
            if appt:
                rx.appointment = appt

        rx.updated_at = datetime.utcnow()
        rx.save()

        return JsonResponse({"message": "Prescription updated"})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ─────────────────────────────────────────
# DELETE  –  DELETE /prescriptions/delete/<id>/
# ─────────────────────────────────────────
@csrf_exempt
def delete_prescription(request, id):
    if request.method != "DELETE":
        return JsonResponse({"error": "Only DELETE allowed"}, status=405)

    try:
        rx = Prescription.objects(id=id).first()
        if not rx:
            return JsonResponse({"error": "Prescription not found"}, status=404)

        rx.delete()
        return JsonResponse({"message": "Prescription deleted"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ═══════════════════════════════════════════════════════════════
# TREATMENT HISTORY VIEWS
# ═══════════════════════════════════════════════════════════════

def _serialize_tx(tx):
    try:
        patient_id = str(tx.patient.id) if tx.patient else None
    except Exception:
        patient_id = None

    try:
        appointment_id = str(tx.appointment.id) if tx.appointment else None
    except Exception:
        appointment_id = None

    return {
        "id":             str(tx.id),
        "patient_id":     patient_id,
        "appointment_id": appointment_id,
        "treatment_text": tx.treatment_text or "",
        "handled_by":     tx.handled_by     or "",
        "procedure_type": tx.procedure_type or "",
        "created_at":     tx.created_at.isoformat() if tx.created_at else None,
        "updated_at":     tx.updated_at.isoformat() if tx.updated_at else None,
    }


# ─────────────────────────────────────────
# LIST  –  GET /treatments/?patient_id=<id>
# ─────────────────────────────────────────
def list_treatments(request):
    patient_id = request.GET.get("patient_id")
    if not patient_id:
        return JsonResponse({"error": "patient_id is required"}, status=400)

    try:
        patient = Patient.objects(id=patient_id).first()
        if not patient:
            return JsonResponse({"error": "Patient not found"}, status=404)

        txs = TreatmentHistory.objects(patient=patient)
        return JsonResponse([_serialize_tx(tx) for tx in txs], safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ─────────────────────────────────────────
# CREATE  –  POST /treatments/create/
# ─────────────────────────────────────────
@csrf_exempt
def create_treatment(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)

        patient_id     = data.get("patient_id")
        appointment_id = data.get("appointment_id")
        treatment_text = data.get("treatment_text", "").strip()
        handled_by     = data.get("handled_by", "").strip()
        procedure_type = data.get("procedure_type", "").strip()

        if not patient_id:
            return JsonResponse({"error": "patient_id is required"}, status=400)
        if not treatment_text:
            return JsonResponse({"error": "treatment_text is required"}, status=400)

        patient = Patient.objects(id=patient_id).first()
        if not patient:
            return JsonResponse({"error": "Patient not found"}, status=404)

        appointment = None
        if appointment_id:
            appointment = Appointment.objects(id=appointment_id).first()

        tx = TreatmentHistory(
            patient        = patient,
            appointment    = appointment,
            treatment_text = treatment_text,
            handled_by     = handled_by,
            procedure_type = procedure_type,
        )
        tx.save()

        return JsonResponse({"message": "Treatment record created", "id": str(tx.id)}, status=201)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ─────────────────────────────────────────
# UPDATE  –  POST /treatments/update/<id>/
# ─────────────────────────────────────────
@csrf_exempt
def update_treatment(request, id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        tx = TreatmentHistory.objects(id=id).first()
        if not tx:
            return JsonResponse({"error": "Treatment record not found"}, status=404)

        data = json.loads(request.body)

        if "treatment_text" in data:
            treatment_text = data["treatment_text"].strip()
            if not treatment_text:
                return JsonResponse({"error": "treatment_text cannot be empty"}, status=400)
            tx.treatment_text = treatment_text

        if "handled_by"     in data: tx.handled_by     = data["handled_by"].strip()
        if "procedure_type" in data: tx.procedure_type = data["procedure_type"].strip()

        if "appointment_id" in data and data["appointment_id"]:
            appt = Appointment.objects(id=data["appointment_id"]).first()
            if appt:
                tx.appointment = appt

        tx.updated_at = datetime.utcnow()
        tx.save()

        return JsonResponse({"message": "Treatment record updated"})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ─────────────────────────────────────────
# DELETE  –  DELETE /treatments/delete/<id>/
# ─────────────────────────────────────────
@csrf_exempt
def delete_treatment(request, id):
    if request.method != "DELETE":
        return JsonResponse({"error": "Only DELETE allowed"}, status=405)

    try:
        tx = TreatmentHistory.objects(id=id).first()
        if not tx:
            return JsonResponse({"error": "Treatment record not found"}, status=404)

        tx.delete()
        return JsonResponse({"message": "Treatment record deleted"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    

def get_patient_detail(request, id):
    try:
        patient = Patient.objects(id=id).first()
        if not patient:
            return JsonResponse({"error": "Patient not found"}, status=404)
        # You would need to serialize the patient here like you do in get_patients
        return JsonResponse({"id": str(patient.id), "name": patient.name, "email": patient.email}) # simplified
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    


@csrf_exempt
def delete_patient(request, id):
    if request.method != "DELETE":
        return JsonResponse({"error": "Only DELETE allowed"}, status=405)
    try:
        patient = Patient.objects(id=id).first()
        if not patient:
            return JsonResponse({"error": "Patient not found"}, status=404)
 
        # Unlink from appointments so they don't become orphaned
        for appt in (patient.appointments or []):
            try:
                appt.patient = None
                appt.save()
            except Exception:
                pass
 
        patient.delete()
        return JsonResponse({"message": "Patient deleted successfully"})
 
    except Exception as e:
        print(f"DELETE PATIENT ERROR: {e}")
        return JsonResponse({"error": str(e)}, status=500)
    














from .models import BillingRecord, Installment, Patient, Appointment
 
 
# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════
 
def _serialize_billing(b):
    try:   patient_id = str(b.patient.id)
    except: patient_id = None
    return {
        "id":           str(b.id),
        "patient_id":   patient_id,
        "total_cost":   b.total_cost   or 0,
        "service_name": b.service_name or "",
        "notes":        b.notes        or "",
        "created_at":   b.created_at.isoformat() if b.created_at else None,
        "updated_at":   b.updated_at.isoformat() if b.updated_at else None,
    }
 
 
def _serialize_installment(inst):
    try:   patient_id = str(inst.patient.id)
    except: patient_id = None
    try:   billing_id = str(inst.billing.id)
    except: billing_id = None
    try:   appointment_id = str(inst.appointment.id) if inst.appointment else None
    except: appointment_id = None
    return {
        "id":             str(inst.id),
        "patient_id":     patient_id,
        "billing_id":     billing_id,
        "appointment_id": appointment_id,
        "amount":         inst.amount        or 0,
        "balance_after":  inst.balance_after or 0,
        "method":         inst.method        or "Cash",
        "service_name":   inst.service_name  or "",
        "notes":          inst.notes         or "",
        "created_at":     inst.created_at.isoformat() if inst.created_at else None,
        "updated_at":     inst.updated_at.isoformat() if inst.updated_at else None,
    }
 
 
def _recalc_balances(patient):
    """Recalculate balance_after for all installments of a patient (oldest first)."""
    billing = BillingRecord.objects(patient=patient).first()
    if not billing:
        return
    total_cost = billing.total_cost or 0
    insts = list(Installment.objects(patient=patient).order_by('created_at'))
    running = 0
    for inst in insts:
        running += inst.amount or 0
        inst.balance_after = max(0, total_cost - running)
        inst.save()
 
 
# ═══════════════════════════════════════════════════════════════
# BILLING RECORD VIEWS
# ═══════════════════════════════════════════════════════════════
 
# GET /billing/?patient_id=<id>
def get_billing(request):
    patient_id = request.GET.get("patient_id")
    if not patient_id:
        return JsonResponse({"error": "patient_id required"}, status=400)
    try:
        patient = Patient.objects(id=patient_id).first()
        if not patient:
            return JsonResponse({"error": "Patient not found"}, status=404)
        b = BillingRecord.objects(patient=patient).first()
        if not b:
            return JsonResponse({}, safe=False)     # no billing yet → empty obj
        return JsonResponse(_serialize_billing(b))
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
# POST /billing/create/
@csrf_exempt
def create_billing(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        data       = json.loads(request.body)
        patient_id = data.get("patient_id")
        total_cost = data.get("total_cost")
 
        if not patient_id:
            return JsonResponse({"error": "patient_id required"}, status=400)
        if total_cost is None or float(total_cost) <= 0:
            return JsonResponse({"error": "total_cost must be positive"}, status=400)
 
        patient = Patient.objects(id=patient_id).first()
        if not patient:
            return JsonResponse({"error": "Patient not found"}, status=404)
 
        # Prevent duplicates — one billing record per patient
        existing = BillingRecord.objects(patient=patient).first()
        if existing:
            return JsonResponse({"error": "Billing record already exists. Use update instead."}, status=400)
 
        b = BillingRecord(
            patient      = patient,
            total_cost   = float(total_cost),
            service_name = data.get("service_name", "").strip(),
            notes        = data.get("notes", "").strip(),
        )
        b.save()
        _recalc_balances(patient)
        return JsonResponse({"message": "Billing record created", "id": str(b.id)}, status=201)
 
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
# POST /billing/update/<id>/
@csrf_exempt
def update_billing(request, id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        b = BillingRecord.objects(id=id).first()
        if not b:
            return JsonResponse({"error": "Billing record not found"}, status=404)
 
        data = json.loads(request.body)
 
        if "total_cost" in data:
            tc = float(data["total_cost"])
            if tc <= 0:
                return JsonResponse({"error": "total_cost must be positive"}, status=400)
            b.total_cost = tc
        if "service_name" in data: b.service_name = data["service_name"].strip()
        if "notes"        in data: b.notes        = data["notes"].strip()
 
        b.updated_at = datetime.utcnow()
        b.save()
        _recalc_balances(b.patient)
        return JsonResponse({"message": "Billing record updated"})
 
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
# ═══════════════════════════════════════════════════════════════
# INSTALLMENT VIEWS
# ═══════════════════════════════════════════════════════════════
 
# GET /installments/?patient_id=<id>
def list_installments(request):
    patient_id = request.GET.get("patient_id")
    if not patient_id:
        return JsonResponse({"error": "patient_id required"}, status=400)
    try:
        patient = Patient.objects(id=patient_id).first()
        if not patient:
            return JsonResponse({"error": "Patient not found"}, status=404)
        insts = Installment.objects(patient=patient).order_by('created_at')
        return JsonResponse([_serialize_installment(i) for i in insts], safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
# POST /installments/create/
@csrf_exempt
def create_installment(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        data       = json.loads(request.body)
        patient_id = data.get("patient_id")
        billing_id = data.get("billing_id")
        amount     = data.get("amount")
 
        if not patient_id:
            return JsonResponse({"error": "patient_id required"}, status=400)
        if not billing_id:
            return JsonResponse({"error": "billing_id required"}, status=400)
        if amount is None or float(amount) <= 0:
            return JsonResponse({"error": "amount must be positive"}, status=400)
 
        patient = Patient.objects(id=patient_id).first()
        if not patient:
            return JsonResponse({"error": "Patient not found"}, status=404)
 
        billing = BillingRecord.objects(id=billing_id).first()
        if not billing:
            return JsonResponse({"error": "Billing record not found"}, status=404)
 
        appointment = None
        if data.get("appointment_id"):
            appointment = Appointment.objects(id=data["appointment_id"]).first()
 
        # Calculate current balance before this installment
        existing_paid = sum(i.amount or 0 for i in Installment.objects(patient=patient))
        balance_after = max(0, (billing.total_cost or 0) - existing_paid - float(amount))
 
        inst = Installment(
            patient       = patient,
            billing       = billing,
            appointment   = appointment,
            amount        = float(amount),
            balance_after = balance_after,
            method        = data.get("method", "Cash"),
            service_name  = data.get("service_name", "").strip(),
            notes         = data.get("notes", "").strip(),
        )
        inst.save()
        return JsonResponse({"message": "Payment recorded", "id": str(inst.id)}, status=201)
 
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
# POST /installments/update/<id>/
@csrf_exempt
def update_installment(request, id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    try:
        inst = Installment.objects(id=id).first()
        if not inst:
            return JsonResponse({"error": "Installment not found"}, status=404)
 
        data = json.loads(request.body)
 
        if "amount" in data:
            amt = float(data["amount"])
            if amt <= 0:
                return JsonResponse({"error": "amount must be positive"}, status=400)
            inst.amount = amt
        if "method"       in data: inst.method       = data["method"]
        if "service_name" in data: inst.service_name = data["service_name"].strip()
        if "notes"        in data: inst.notes        = data["notes"].strip()
        if "appointment_id" in data and data["appointment_id"]:
            appt = Appointment.objects(id=data["appointment_id"]).first()
            if appt: inst.appointment = appt
 
        inst.updated_at = datetime.utcnow()
        inst.save()
 
        # Recalculate all balances
        _recalc_balances(inst.patient)
        return JsonResponse({"message": "Payment updated"})
 
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
# DELETE /installments/delete/<id>/
@csrf_exempt
def delete_installment(request, id):
    if request.method != "DELETE":
        return JsonResponse({"error": "Only DELETE allowed"}, status=405)
    try:
        inst = Installment.objects(id=id).first()
        if not inst:
            return JsonResponse({"error": "Installment not found"}, status=404)
        patient = inst.patient
        inst.delete()
        _recalc_balances(patient)
        return JsonResponse({"message": "Payment deleted"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 





import os
import uuid
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from mongoengine.errors import DoesNotExist
from .models import GalleryImage, Service
import json

# ─────────────────────────────────────────
# Allowed file config
# ─────────────────────────────────────────
ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
ALLOWED_VIDEO_TYPES = {'video/mp4', 'video/webm', 'video/ogg', 'video/quicktime'}
MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10 MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB

MEDIA_ROOT = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
MEDIA_URL  = getattr(settings, 'MEDIA_URL',  '/media/')


def _save_file(uploaded_file, sub_folder):
    """Save an uploaded file to media/<sub_folder>/ with a UUID name."""
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    folder = os.path.join(MEDIA_ROOT, sub_folder)
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)
    with open(filepath, 'wb+') as dest:
        for chunk in uploaded_file.chunks():
            dest.write(chunk)
    return f"{sub_folder}/{filename}"   # relative path stored in DB


def _public_url(relative_path):
    """Convert a relative media path to a full URL."""
    if not relative_path:
        return None
    request_base = getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000')
    return f"{request_base}{MEDIA_URL}{relative_path}"


# ─────────────────────────────────────────
# UPLOAD  (POST /gallery/upload/)
# ─────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST"])
def upload_gallery_media(request):
    """
    Accepts multipart/form-data with:
      - files[]      : one or more image / video files
      - service_id   : (optional) MongoEngine ObjectId string
      - description  : (optional) text
    Returns list of created gallery items.
    """
    files       = request.FILES.getlist('files[]')
    service_id  = request.POST.get('service_id', '').strip()
    description = request.POST.get('description', '').strip()

    if not files:
        return JsonResponse({'error': 'No files provided.'}, status=400)

    # Resolve service reference (optional)
    service = None
    if service_id:
        try:
            service = Service.objects.get(id=service_id)
        except (DoesNotExist, Exception):
            return JsonResponse({'error': 'Invalid service_id.'}, status=400)

    created = []
    errors  = []

    for f in files:
        content_type = f.content_type
        is_image = content_type in ALLOWED_IMAGE_TYPES
        is_video = content_type in ALLOWED_VIDEO_TYPES

        # ── Validation ──────────────────────────────
        if not (is_image or is_video):
            errors.append(f"{f.name}: unsupported file type ({content_type}).")
            continue

        if is_image and f.size > MAX_IMAGE_SIZE:
            errors.append(f"{f.name}: image exceeds 10 MB limit.")
            continue

        if is_video and f.size > MAX_VIDEO_SIZE:
            errors.append(f"{f.name}: video exceeds 100 MB limit.")
            continue

        # ── Save & persist ───────────────────────────
        try:
            if is_image:
                rel_path = _save_file(f, 'gallery/images')
                item = GalleryImage(
                    image=rel_path,
                    description=description,
                )
            else:
                rel_path = _save_file(f, 'gallery/videos')
                item = GalleryImage(
                    video=rel_path,
                    description=description,
                )

            if service:
                item.service = service

            item.save()

            created.append({
                'id':          str(item.id),
                'type':        'image' if is_image else 'video',
                'url':         _public_url(item.image if is_image else item.video),
                'description': item.description,
                'service':     service.name if service else None,
                'created_at':  item.created_at.isoformat(),
            })

        except Exception as e:
            errors.append(f"{f.name}: upload failed — {str(e)}")

    response = {'created': created}
    if errors:
        response['errors'] = errors

    status = 201 if created else 400
    return JsonResponse(response, status=status)


# ─────────────────────────────────────────
# FETCH  (GET /gallery/)
# ─────────────────────────────────────────
@require_http_methods(["GET"])
def get_gallery(request):
    """
    Query params:
      - type        : 'image' | 'video' | 'all'  (default: 'all')
      - service_id  : filter by service
      - page        : page number (default 1)
      - limit       : items per page (default 20, max 50)
    """
    media_type = request.GET.get('type', 'all')
    service_id = request.GET.get('service_id', '').strip()
    page       = max(1, int(request.GET.get('page', 1)))
    limit      = min(50, max(1, int(request.GET.get('limit', 20))))

    qs = GalleryImage.objects.all()

    # ── Filters ─────────────────────────────────────
    if media_type == 'image':
        qs = qs.filter(image__exists=True, video=None)
    elif media_type == 'video':
        qs = qs.filter(video__exists=True, image=None)

    if service_id:
        try:
            qs = qs.filter(service=service_id)
        except Exception:
            pass

    total  = qs.count()
    offset = (page - 1) * limit
    items  = qs.skip(offset).limit(limit)

    results = []
    for item in items:
        is_image = bool(item.image)
        results.append({
            'id':          str(item.id),
            'type':        'image' if is_image else 'video',
            'url':         _public_url(item.image if is_image else item.video),
            'description': item.description or '',
            'service':     item.service.name if item.service else None,
            'service_id':  str(item.service.id) if item.service else None,
            'created_at':  item.created_at.isoformat(),
        })

    return JsonResponse({
        'results':      results,
        'total':        total,
        'page':         page,
        'limit':        limit,
        'total_pages':  (total + limit - 1) // limit,
    })


# ─────────────────────────────────────────
# DELETE  (DELETE /gallery/delete/<id>/)
# ─────────────────────────────────────────
@csrf_exempt
@require_http_methods(["DELETE"])
def delete_gallery_item(request, item_id):
    """Deletes a gallery item and removes its file from disk."""
    try:
        item = GalleryImage.objects.get(id=item_id)
    except (DoesNotExist, Exception):
        return JsonResponse({'error': 'Item not found.'}, status=404)

    # Delete the physical file
    rel_path = item.image or item.video
    if rel_path:
        full_path = os.path.join(MEDIA_ROOT, rel_path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except OSError:
                pass   # log and continue; DB record will still be removed

    item.delete()
    return JsonResponse({'success': True, 'deleted_id': item_id})


# ─────────────────────────────────────────
# UPDATE DESCRIPTION  (PATCH /gallery/update/<id>/)
# ─────────────────────────────────────────
@csrf_exempt
@require_http_methods(["PATCH"])
def update_gallery_item(request, item_id):
    try:
        item = GalleryImage.objects.get(id=item_id)
    except (DoesNotExist, Exception):
        return JsonResponse({'error': 'Item not found.'}, status=404)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    if 'description' in body:
        item.description = body['description']

    item.save()
    return JsonResponse({'success': True, 'description': item.description})




"""
security/views.py
──────────────────
All security-related Django views (no DRF) using MongoEngine.
"""

import json
import logging

from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone

from .models import UserProfile, OTPCode, UserSession
from .utils import (
    validate_password_strength,
    send_sms_otp,
    send_email_otp,
    generate_totp_secret,
    generate_totp_qr_base64,
    verify_totp_code,
    get_client_ip,
    get_user_agent,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

# def _require_auth(request):
#     """Return user or None."""
#     if request.user.is_authenticated:
#         return request.user
#     return None

def _require_auth(request):
    """Return user or None."""
    if request.user.is_authenticated:
        return request.user
    return None



# _get_or_create_profile is defined above (auth section)


def _json_body(request) -> tuple[dict, JsonResponse | None]:
    try:
        return json.loads(request.body), None
    except (json.JSONDecodeError, ValueError):
        return {}, JsonResponse({"error": "Invalid JSON body"}, status=400)


def _register_session(user, request):
    """Track this session in UserSession for log-out-all support."""
    sk = request.session.session_key
    if sk:
        UserSession.objects(session_key=sk).update_one(
            upsert=True,
            user_id=str(user.id),
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            is_active=True,
        )


# ─────────────────────────────────────────────────────────────────────────────
#  1. CHANGE PASSWORD
# ─────────────────────────────────────────────────────────────────────────────

# @csrf_exempt
# @require_POST
# def change_password_view(request):
#     user = _require_auth(request)
#     if not user:
#         return JsonResponse({"detail": "Authentication required"}, status=401)

#     data, err = _json_body(request)
#     if err:
#         return err

#     current_password = data.get("current_password", "").strip()
#     new_password     = data.get("new_password", "").strip()
#     confirm_password = data.get("confirm_password", "").strip()

#     # ── Validate current password ─────────────────────────────────────────
#     if not current_password:
#         return JsonResponse({"error": "Current password is required."}, status=400)

#     if not user.check_password(current_password):
#         return JsonResponse({"error": "Current password is incorrect."}, status=400)

#     # ── Validate new password rules ───────────────────────────────────────
#     if not new_password:
#         return JsonResponse({"error": "New password is required."}, status=400)

#     strength_errors = validate_password_strength(new_password)
#     if strength_errors:
#         return JsonResponse({"error": strength_errors[0], "errors": strength_errors}, status=400)

#     if new_password != confirm_password:
#         return JsonResponse({"error": "New passwords do not match."}, status=400)

#     if new_password == current_password:
#         return JsonResponse({"error": "New password must be different from the current one."}, status=400)

#     # ── Apply change ──────────────────────────────────────────────────────
#     user.set_password(new_password)
#     user.save()

#     # Keep current session alive after password change
#     update_session_auth_hash(request, user)

#     logger.info(f"Password changed for user {user.username}")
#     return JsonResponse({"detail": "Password changed successfully."})


# ─────────────────────────────────────────────────────────────────────────────
#  2. 2FA STATUS — GET current 2FA flags from UserProfile
# ─────────────────────────────────────────────────────────────────────────────

# @csrf_exempt
# @require_GET
# def get_2fa_status(request):
#     user = _require_auth(request)
#     if not user:
#         return JsonResponse({"detail": "Authentication required"}, status=401)

#     profile = _get_or_create_profile(user)

#     return JsonResponse({
#         "sms_2fa_enabled":   profile.sms_2fa_enabled,
#         "app_2fa_enabled":   profile.app_2fa_enabled,
#         "email_2fa_enabled": profile.email_2fa_enabled,
#         "totp_verified":     profile.totp_verified,
#         "phone":             profile.phone,
#         "email":             user.email,
#     })


# # ─────────────────────────────────────────────────────────────────────────────
# #  3. TOGGLE 2FA
# # ─────────────────────────────────────────────────────────────────────────────

# @csrf_exempt
# @require_POST
# def toggle_2fa(request):
#     user = _require_auth(request)
#     if not user:
#         return JsonResponse({"detail": "Authentication required"}, status=401)

#     data, err = _json_body(request)
#     if err:
#         return err

#     method  = data.get("method", "")
#     enabled = bool(data.get("enabled", False))

#     profile = _get_or_create_profile(user)

#     if method == "sms":
#         if enabled and not profile.phone:
#             return JsonResponse(
#                 {"error": "A phone number is required to enable SMS authentication. "
#                           "Please update your profile first."},
#                 status=400,
#             )
#         profile.sms_2fa_enabled = enabled
#         profile.save()
#         return JsonResponse({
#             "detail": f"SMS 2FA {'enabled' if enabled else 'disabled'}.",
#             "sms_2fa_enabled": profile.sms_2fa_enabled,
#         })

#     elif method == "email":
#         if enabled and not user.email:
#             return JsonResponse(
#                 {"error": "No email address on your account. Please update your profile first."},
#                 status=400,
#             )
#         profile.email_2fa_enabled = enabled
#         profile.save()
#         return JsonResponse({
#             "detail": f"Email 2FA {'enabled' if enabled else 'disabled'}.",
#             "email_2fa_enabled": profile.email_2fa_enabled,
#         })

#     elif method == "app":
#         if enabled and not profile.totp_verified:
#             return JsonResponse(
#                 {"error": "Complete Authenticator App setup first via /security/2fa/totp/setup/."},
#                 status=400,
#             )
#         profile.app_2fa_enabled = enabled
#         if not enabled:
#             profile.totp_secret = ""
#             profile.totp_verified = False
#         profile.save()

#         return JsonResponse({
#             "detail": f"Authenticator App 2FA {'enabled' if enabled else 'disabled'}.",
#             "app_2fa_enabled": profile.app_2fa_enabled,
#         })

#     return JsonResponse({"error": "Invalid 2FA method. Use 'sms', 'email', or 'app'."}, status=400)


# # ─────────────────────────────────────────────────────────────────────────────
# #  4. TOTP SETUP — Generate secret + QR code for Authenticator App
# # ─────────────────────────────────────────────────────────────────────────────

# @csrf_exempt
# def totp_setup(request):
#     user = _require_auth(request)
#     if not user:
#         return JsonResponse({"detail": "Authentication required"}, status=401)

#     profile = _get_or_create_profile(user)

#     # Always regenerate a fresh secret during setup (not yet verified)
#     secret = generate_totp_secret()
#     profile.totp_secret = secret
#     profile.totp_verified = False
#     profile.app_2fa_enabled = False
#     profile.save()

#     qr_b64 = generate_totp_qr_base64(secret, user.username)

#     return JsonResponse({
#         "secret":    secret,
#         "qr_code":   qr_b64,
#         "detail":    "Scan the QR code in Google Authenticator or Authy, then confirm with a 6-digit code.",
#     })


# # ─────────────────────────────────────────────────────────────────────────────
# #  5. TOTP VERIFY SETUP
# # ─────────────────────────────────────────────────────────────────────────────

# @csrf_exempt
# @require_POST
# def totp_verify_setup(request):
#     user = _require_auth(request)
#     if not user:
#         return JsonResponse({"detail": "Authentication required"}, status=401)

#     data, err = _json_body(request)
#     if err:
#         return err

#     code = str(data.get("code", "")).strip()
#     if not code:
#         return JsonResponse({"error": "Verification code is required."}, status=400)

#     profile = _get_or_create_profile(user)

#     if not profile.totp_secret:
#         return JsonResponse(
#             {"error": "No TOTP setup in progress. Call /security/2fa/totp/setup/ first."},
#             status=400,
#         )

#     if verify_totp_code(profile.totp_secret, code):
#         profile.totp_verified = True
#         profile.app_2fa_enabled = True
#         profile.save()
#         return JsonResponse({
#             "detail": "Authenticator App 2FA is now active.",
#             "app_2fa_enabled": True,
#             "totp_verified":   True,
#         })
#     else:
#         return JsonResponse({"error": "Invalid or expired code. Please try again."}, status=400)


# # ─────────────────────────────────────────────────────────────────────────────
# #  6. SEND OTP
# # ─────────────────────────────────────────────────────────────────────────────

# @csrf_exempt
# @require_POST
# def send_otp(request):
#     user = _require_auth(request)
#     if not user:
#         return JsonResponse({"detail": "Authentication required"}, status=401)

#     data, err = _json_body(request)
#     if err:
#         return err

#     method = data.get("method", "")

#     profile = _get_or_create_profile(user)

#     if method == "sms":
#         phone = profile.phone
#         if not phone:
#             return JsonResponse({"error": "No phone number saved on your profile."}, status=400)

#         otp = OTPCode.generate(str(user.id), purpose="sms_login")
#         success = send_sms_otp(phone, otp.code)
#         if not success:
#             return JsonResponse({"error": "Failed to send SMS. Please try again."}, status=500)
#         return JsonResponse({"detail": f"OTP sent to {phone[-4:].rjust(len(phone), '*')}."})

#     elif method == "email":
#         email = user.email
#         if not email:
#             return JsonResponse({"error": "No email address on your account."}, status=400)

#         otp = OTPCode.generate(str(user.id), purpose="email_login")
#         success = send_email_otp(email, otp.code, purpose="login")
#         if not success:
#             return JsonResponse({"error": "Failed to send email. Please try again."}, status=500)
#         masked = email[:2] + "***" + email[email.find("@"):]
#         return JsonResponse({"detail": f"OTP sent to {masked}."})

#     return JsonResponse({"error": "Invalid method. Use 'sms' or 'email'."}, status=400)


# # ─────────────────────────────────────────────────────────────────────────────
# #  7. VERIFY OTP
# # ─────────────────────────────────────────────────────────────────────────────

# @csrf_exempt
# @require_POST
# def verify_otp(request):
#     user = _require_auth(request)
#     if not user:
#         return JsonResponse({"detail": "Authentication required"}, status=401)

#     data, err = _json_body(request)
#     if err:
#         return err

#     method = data.get("method", "")
#     code   = str(data.get("code", "")).strip()

#     if not code:
#         return JsonResponse({"error": "Verification code is required."}, status=400)

#     purpose_map = {"sms": "sms_login", "email": "email_login"}
#     purpose = purpose_map.get(method)
#     if not purpose:
#         return JsonResponse({"error": "Invalid method."}, status=400)

#     valid = OTPCode.verify(str(user.id), purpose=purpose, code=code)
#     if valid:
#         return JsonResponse({"detail": "Verification successful.", "verified": True})
#     return JsonResponse({"error": "Invalid or expired code.", "verified": False}, status=400)


# ─────────────────────────────────────────────────────────────────────────────
#  8. LOG OUT ALL SESSIONS
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
@require_POST
def logout_all_sessions(request):
    user = _require_auth(request)
    if not user:
        return JsonResponse({"detail": "Authentication required"}, status=401)

    current_session_key = request.session.session_key

    # ── Find all session keys for this user in our tracker ────────────────
    user_sessions = UserSession.objects(user_id=str(user.id), is_active=True)
    session_keys = [us.session_key for us in user_sessions]

    # ── Delete from Django's session store ───────────────────────────────
    deleted_count = 0
    for sk in session_keys:
        try:
            Session.objects.get(session_key=sk).delete()
            deleted_count += 1
        except Session.DoesNotExist:
            pass

    # ── Mark all as inactive in our tracker ──────────────────────────────
    user_sessions.update(is_active=False)

    # ── Log out current request session too ───────────────────────────────
    logout(request)

    logger.info(f"Logged out all {deleted_count} sessions for user {user.username}")

    return JsonResponse({
        "detail": f"All sessions terminated ({deleted_count} device(s) signed out).",
        "logged_out": True,
    })


# ─────────────────────────────────────────────────────────────────────────────
#  9. DELETE ACCOUNT
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
@require_POST
def delete_account(request):
    user = _require_auth(request)
    if not user:
        return JsonResponse({"detail": "Authentication required"}, status=401)

    data, err = _json_body(request)
    if err:
        return err

    password     = data.get("password", "").strip()
    confirm_text = data.get("confirm_text", "").strip()

    if confirm_text != "DELETE":
        return JsonResponse(
            {"error": 'Type exactly "DELETE" to confirm account deletion.'},
            status=400,
        )

    if not password:
        return JsonResponse({"error": "Password is required to delete your account."}, status=400)

    if not user.check_password(password):
        return JsonResponse({"error": "Incorrect password."}, status=400)

    user_id   = str(user.id)
    username  = user.username

    # ── Delete all related security data using MongoEngine ─────────────────
    OTPCode.objects(user_id=user_id).delete()
    UserSession.objects(user_id=user_id).delete()
    UserProfile.objects(user_id=user_id).delete()

    # ── Terminate all sessions first ─────────────────────────────────────
    logout(request)

    # ── Delete Django user (cascades to auth tables) ──────────────────────
    user.delete()

    logger.warning(f"Account permanently deleted: {username} (id={user_id})")

    return JsonResponse({
        "detail": "Account permanently deleted.",
        "deleted": True,
    })


# ─────────────────────────────────────────────────────────────────────────────
#  10. LOGOUT (single session)
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
@require_POST
def logout_view(request):
    sk = request.session.session_key
    if sk:
        UserSession.objects(session_key=sk).update(is_active=False)
    logout(request)
    return JsonResponse({"detail": "Logged out successfully."})