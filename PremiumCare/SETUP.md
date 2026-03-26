# MedPlatform — Setup Guide

## Requirements
- Python 3.9+
- PostgreSQL 13+

## Step 1 — Edit config.py
Open `config.py` and update:
  - `DB_CONFIG` → your PostgreSQL host/user/password
  - `SECRET_KEY` → any long random string (change this!)
  - `ANTHROPIC_API_KEY` → from console.anthropic.com
  - `PRACTICE_NAME` → your practice name

## Step 2 — Create the Database (ONE TIME ONLY)
  psql -U medplatform_user -d medplatform -f setup_database.sql

## Step 3 — Install Python Packages
  pip install -r requirements.txt

## Step 4 — Start the App
  python app.py

## Step 5 — Open Browser
  http://localhost:5000
  Email:    admin@practice.local
  Password: admin123

## Features
  - Dashboard with AI usage stats
  - Patient management (CRUD, visit notes, appointment history)
  - AI Clinical Assistant (hero feature — differential dx, drug checks, treatment plans)
  - AI Symptom Analysis per patient
  - AI Scan Analysis (image upload)
  - Calendar & Appointments
  - Team Management
  - Activity Log

## After First Login
  - Change admin password immediately
  - Set your ANTHROPIC_API_KEY in config.py
  - Update PRACTICE_NAME in config.py

## Load Sample Data (Optional but Recommended for Testing)

Run this AFTER setup_database.sql to populate all tables with realistic test data:

  psql -U medplatform_user -d medplatform -f seed_data.sql

### What the seed data includes:
  - 7 staff members (doctors, nurses, receptionist)
  - 12 patients with full medical histories, allergies, vitals
  - 25+ appointments (scheduled, completed, cancelled)
  - 8 visit/consultation notes (SOAP format)
  - 21 prescriptions (active and completed)
  - 21 lab tests (normal, abnormal, pending)
  - 19 invoices (paid, partial, unpaid, overdue) for finance charts
  - 16 vaccinations with due dates
  - 7 referral letters (draft, sent, completed)
  - 7 recalls (active and returned)
  - 11 reminders (pending and completed)
  - 12 patient documents
  - 10 address book contacts (specialists, hospital, pharmacy)
  - 7 inbox messages (unread and read)
  - 3 waiting room entries
  - 2 AI symptom analyses
  - 4 consultation notes (SOAP)
  - Activity log with 18 entries

### Test Login Credentials:
  Admin:      admin@practice.local      / admin123
  Doctor 1:   elena.marchetti@practice.local / admin123
  Doctor 2:   james.okonkwo@practice.local   / admin123
  Nurse:      maria.santos@practice.local    / admin123
  Reception:  lisa.chen@practice.local       / admin123
