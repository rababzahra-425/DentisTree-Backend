from django.urls import path
from . import views
from .views import login_view, logout_view, check_auth
from .cookie_consent_views import record_cookie_consent


urlpatterns = [

    path("cookie-consent/", record_cookie_consent, name="cookie_consent"),

    # Service
    path('services/create/', views.create_service),
    path('services/', views.get_services),
    path('services/update/<str:id>/', views.update_service),
    path('services/delete/<str:id>/', views.delete_service),

    # Appointment
    path('appointments/create/', views.create_appointment),
    path('appointments/poll/', views.appointments_poll_view),
    path('appointments/', views.get_appointments),
    path('appointments/update/<str:id>/', views.update_appointment_status),

    # Payment
    path('payments/create_or_update/', views.create_or_update_payment),
    path('payments/create/', views.create_payment),
    path('payments/', views.get_payments),

    # Financial Report
    path('reports/financial/', views.financial_report),

    # Reviews
    path('reviews/create/', views.create_review),
    path('reviews/', views.get_reviews),
    path('reviews/delete/<str:id>/', views.delete_review),
 

    # path('patients/create/', views.create_patient),
    # path('patients/', views.get_patients),
    path('patients/poll/',           views.patients_poll_view, name='patients_poll'),
    path('patients/',                views.get_patients,    name='get_patients'),
    path('patients/create/',         views.create_patient,  name='create_patient'),
    path('patients/update/<str:id>/',views.update_patient,  name='update_patient'),
    path('patients/<str:id>/', views.get_patient_detail, name='get_patient_detail'),
    path('patients/delete/<str:id>/', views.delete_patient, name='delete_patient'),
    # path('before-after/', views.get_before_after_images),

    # path('before-after/create/', views.create_before_after),        # ← was 'add/', change to 'create/'
    # path('before-after/update/<str:id>/', views.update_before_after_image),
    # path('before-after/delete/<str:id>/', views.delete_before_after_image),
    path("gallery/", views.list_gallery, name="gallery-list"),

    # CREATE –  /gallery/create/
    path("gallery/create/", views.create_gallery, name="gallery-create"),
    
    # DETAIL –  /gallery/<id>/
    path("gallery/<str:id>/", views.detail_gallery, name="gallery-detail"),
 
    # UPDATE –  /gallery/update/<id>/
    path("gallery/update/<str:id>/", views.update_gallery, name="gallery-update"),
 
    # DELETE –  /gallery/delete/<id>/
    path("gallery/delete/<str:id>/", views.delete_gallery, name="gallery-delete"),


    
    path('employees/', views.get_employees),
    path('employees/create/', views.create_employee),
    path('employees/update/<str:id>/', views.update_employee),
    path('employees/delete/<str:id>/', views.delete_employee),
    path('employees/salary-status/<str:id>/', views.update_salary_status),
    path('employees/salary/reset-all/', views.reset_all_salary_status),


    path('suppliers/', views.get_suppliers),
    path('suppliers/create/', views.create_supplier),
    path('suppliers/update/<str:id>/', views.update_supplier),
    path('suppliers/delete/<str:id>/', views.delete_supplier),
 
    # Inventory
    path('inventory/', views.get_inventory),
    path('inventory/create/', views.create_inventory_item),
    path('inventory/update/<str:id>/', views.update_inventory_item),
    path('inventory/adjust/<str:id>/', views.adjust_stock),
    path('inventory/delete/<str:id>/', views.delete_inventory_item),

        # Expenses & Financial Summary
    path('expenses/', views.get_expenses),
    path('expenses/create/', views.create_expense),
    path('expenses/update/<str:id>/', views.update_expense),
    path('expenses/delete/<str:id>/', views.delete_expense),
    path('expenses/summary/', views.get_financial_summary),
    path('reports/financial/', views.financial_report),
    
    path('dashboard/poll/', views.dashboard_poll_view),
    path('dashboard/', views.get_dashboard),
    




    # path('login/', login_view),
    # path('logout/', logout_view),
    # path('check-auth/', check_auth),
    # path('auth/login/',    views.login_view,    name='login'),
    # path('auth/check/',    views.auth_check,    name='auth_check'),

    path('auth/login/', views.login_view, name='auth-login'),
    path('auth/csrf/', views.csrf_token_view, name='auth-csrf'),
    path('auth/me/', views.auth_me_view, name='auth-me'),
    path('auth/check/', views.check_auth, name='auth-check'),  # session probe
 
    # POST /auth/profile/update/
    # path('profile/update/', views.update_profile_view, name='auth-profile-update'),
 


    # ── Settings ────────────────────────────────────────────────────
    path('settings/update-profile/',   views.update_profile_view,  name='update_profile'),
    path('settings/change-password/',  views.change_password_view, name='change_password'),
    path('settings/notifications/',    views.get_notifications_view, name='get_notifications'),
    path('settings/notifications/update/', views.update_notifications_view, name='update_notifications'),
    path('notifications/feed/', views.notification_feed_view, name='notification_feed'),
    path('notifications/unread-count/', views.notification_unread_count_view, name='notification_unread_count'),
    path('notifications/mark-all-read/', views.notification_mark_all_read_view, name='notification_mark_all_read'),
    path('notifications/<str:notif_id>/read/', views.notification_mark_read_view, name='notification_mark_read'),




    # ─────────────────────────────────────────
    # PRESCRIPTION ROUTES
    # ─────────────────────────────────────────
    # GET  /prescriptions/?patient_id=<id>    → list all prescriptions for a patient
    path('prescriptions/',                 views.list_prescriptions,   name='list_prescriptions'),
 
    # POST /prescriptions/create/            → create new prescription
    path('prescriptions/create/',          views.create_prescription,  name='create_prescription'),
 
    # POST /prescriptions/update/<id>/       → update existing prescription
    path('prescriptions/update/<str:id>/', views.update_prescription,  name='update_prescription'),
 
    # DELETE /prescriptions/delete/<id>/     → delete prescription
    path('prescriptions/delete/<str:id>/', views.delete_prescription,  name='delete_prescription'),
 
    # ─────────────────────────────────────────
    # TREATMENT HISTORY ROUTES
    # ─────────────────────────────────────────
    # GET  /treatments/?patient_id=<id>      → list all treatment records for a patient
    path('treatments/',                    views.list_treatments,      name='list_treatments'),
 
    # POST /treatments/create/               → create new treatment record
    path('treatments/create/',             views.create_treatment,     name='create_treatment'),
 
    # POST /treatments/update/<id>/          → update treatment record
    path('treatments/update/<str:id>/',    views.update_treatment,     name='update_treatment'),
 
    # DELETE /treatments/delete/<id>/        → delete treatment record
    path('treatments/delete/<str:id>/',    views.delete_treatment,     name='delete_treatment'),





     path('billing/',                    views.get_billing,          name='get_billing'),
 
    # POST /billing/create/            → create billing record
    path('billing/create/',             views.create_billing,       name='create_billing'),
 
    # POST /billing/update/<id>/       → update billing record
    path('billing/update/<str:id>/',    views.update_billing,       name='update_billing'),
 
    # ─────────────────────────────────────────
    # INSTALLMENT ROUTES
    # ─────────────────────────────────────────
    # GET  /installments/?patient_id=<id>   → list installments for patient
    path('installments/',                    views.list_installments,    name='list_installments'),
 
    # POST /installments/create/            → add a payment installment
    path('installments/create/',             views.create_installment,   name='create_installment'),
 
    # POST /installments/update/<id>/       → edit an installment
    path('installments/update/<str:id>/',    views.update_installment,   name='update_installment'),
 
    # DELETE /installments/delete/<id>/     → delete an installment
    path('installments/delete/<str:id>/',    views.delete_installment,   name='delete_installment'),

    # POST /auth/change-password/
    path('change-password/', views.change_password_view, name='change_password'),
    path('auth/logout/',   views.logout_view,   name='auth_logout'),
    # path("security/2fa/status/", views.get_2fa_status, name="2fa_status"),
 
    # ── Toggle 2FA ────────────────────────────────────────────────────────
    # POST  /security/2fa/toggle/
    # Body: { "method": "sms"|"email"|"app", "enabled": true|false }
    # path("security/2fa/toggle/", views.toggle_2fa, name="2fa_toggle"),
 
    # ── TOTP (Authenticator App) Setup ────────────────────────────────────
    # GET   /security/2fa/totp/setup/   → returns secret + QR code
    # path("security/2fa/totp/setup/", views.totp_setup, name="totp_setup"),
 
    # ── TOTP Verify Setup ─────────────────────────────────────────────────
    # POST  /security/2fa/totp/verify-setup/
    # Body: { "code": "123456" }
    # path("security/2fa/totp/verify-setup/", views.totp_verify_setup, name="totp_verify_setup"),
 
    # ── Send OTP (SMS or Email) ───────────────────────────────────────────
    # POST  /security/2fa/otp/send/
    # Body: { "method": "sms" | "email" }
    # path("security/2fa/otp/send/", views.send_otp, name="send_otp"),
 
    # ── Verify OTP ────────────────────────────────────────────────────────
    # POST  /security/2fa/otp/verify/
    # Body: { "method": "sms" | "email", "code": "123456" }
    # path("security/2fa/otp/verify/", views.verify_otp, name="verify_otp"),
 
    # ── Danger Zone ───────────────────────────────────────────────────────
    # POST  /security/logout-all/
    path("security/logout-all/", views.logout_all_sessions, name="logout_all"),
 
    # POST  /security/delete-account/
    # Body: { "password": "...", "confirm_text": "DELETE" }
    path("security/delete-account/", views.delete_account, name="delete_account"),
    # path('notifications/<str:notif_id>/delete/', notification_delete_view, name='notification-delete'),
    path('notifications/<str:notif_id>/delete/', views.notification_delete_view),

]