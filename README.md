# Dentis Tree Dental Clinic - Backend

A comprehensive backend system for managing dental clinic operations, built with Django and Django REST Framework.

## Features

- User Authentication & Authorization
- Patient Management
- Appointment Scheduling
- Dentist Management
- Services Management
- Payment Management
- Admin Dashboard APIs
- RESTful API Architecture
- Database Integration
- Secure Environment Configuration

## Tech Stack

- Django
- MongoDB
- Session Based Authentication
- Gunicorn

## Purpose

This backend powers the Dentis Tree Dental Clinic Management System by providing secure APIs and business logic for managing clinic operations.

```
source venv/bin/activate
nohup gunicorn project.wsgi:application --bind 127.0.0.1:8005 --workers 3 > gunicorn.log 2>&1 &
```