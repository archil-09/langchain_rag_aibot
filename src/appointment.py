"""
appointment.py — Handles booking, rescheduling, cancelling appointments
Uses a CSV file to store appointments
"""

import csv
import os
from datetime import datetime

APPOINTMENTS_FILE = "appointments/appointments.csv"
HEADERS = ["Name", "Phone", "Treatment", "Date", "Time", "Status"]

# ── Ensure CSV file exists with headers ────────────────────────────
def init_appointments_file():
    """Create appointments CSV if it doesn't exist"""
    os.makedirs("appointments", exist_ok=True)
    if not os.path.exists(APPOINTMENTS_FILE):
        with open(APPOINTMENTS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(HEADERS)
        print("Appointments file created.")


# ── Read all appointments ───────────────────────────────────────────
def read_appointments() -> list[dict]:
    """Return all appointments as list of dicts"""
    init_appointments_file()
    with open(APPOINTMENTS_FILE, "r") as f:
        reader = csv.DictReader(f)
        return list(reader)


# ── Write all appointments ──────────────────────────────────────────
def write_appointments(appointments: list[dict]):
    """Overwrite CSV with updated appointments list"""
    with open(APPOINTMENTS_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(appointments)


# ── Book new appointment ────────────────────────────────────────────
def book_appointment(name: str, phone: str, treatment: str, date: str, time: str) -> str:
    """Add new appointment to CSV"""
    init_appointments_file()

    # Check if patient already has a booked appointment
    appointments = read_appointments()
    for apt in appointments:
        if apt["Phone"] == phone and apt["Status"] == "Booked":
            return (
                f"You already have an appointment on {apt['Date']} at {apt['Time']} "
                f"for {apt['Treatment']}. "
                f"Would you like to reschedule it instead?"
            )

    # Add new appointment
    with open(APPOINTMENTS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([name, phone, treatment, date, time, "Booked"])

    return (
        f"✅ Appointment confirmed!\n\n"
        f"👤 Name: {name}\n"
        f"🦷 Treatment: {treatment}\n"
        f"📅 Date: {date}\n"
        f"⏰ Time: {time}\n\n"
        f"We'll send you a reminder the day before. "
        f"To reschedule, just message us anytime!"
    )


# ── Reschedule appointment ──────────────────────────────────────────
def reschedule_appointment(phone: str, new_date: str, new_time: str) -> str:
    """Update existing appointment with new date and time"""
    appointments = read_appointments()
    updated = False

    for apt in appointments:
        if apt["Phone"] == phone and apt["Status"] == "Booked":
            old_date = apt["Date"]
            old_time = apt["Time"]
            apt["Date"] = new_date
            apt["Time"] = new_time
            updated = True
            break

    if updated:
        write_appointments(appointments)
        return (
            f"✅ Appointment rescheduled!\n\n"
            f"📅 New Date: {new_date}\n"
            f"⏰ New Time: {new_time}\n\n"
            f"Previous appointment ({old_date} at {old_time}) has been cancelled."
        )
    else:
        return (
            "I couldn't find an active appointment for your number. "
            "Would you like to book a new appointment?"
        )


# ── Cancel appointment ──────────────────────────────────────────────
def cancel_appointment(phone: str) -> str:
    """Mark appointment as cancelled"""
    appointments = read_appointments()
    cancelled = False

    for apt in appointments:
        if apt["Phone"] == phone and apt["Status"] == "Booked":
            apt["Status"] = "Cancelled"
            cancelled = True
            break

    if cancelled:
        write_appointments(appointments)
        return (
            "✅ Your appointment has been cancelled.\n"
            "We hope to see you soon! Message us anytime to rebook."
        )
    else:
        return "I couldn't find an active appointment for your number."


# ── Check appointment status ────────────────────────────────────────
def get_appointment(phone: str) -> str:
    """Return appointment details for a phone number"""
    appointments = read_appointments()

    for apt in appointments:
        if apt["Phone"] == phone and apt["Status"] == "Booked":
            return (
                f"📋 Your appointment details:\n\n"
                f"👤 Name: {apt['Name']}\n"
                f"🦷 Treatment: {apt['Treatment']}\n"
                f"📅 Date: {apt['Date']}\n"
                f"⏰ Time: {apt['Time']}\n"
                f"Status: {apt['Status']}\n\n"
                f"To reschedule or cancel, just let us know!"
            )

    return (
        "I couldn't find any active appointment for your number. "
        "Would you like to book one?"
    )


# ── Get appointments for reminder (tomorrow's) ──────────────────────
def get_tomorrows_appointments() -> list[dict]:
    """Return all appointments scheduled for tomorrow"""
    from datetime import timedelta
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    appointments = read_appointments()
    return [
        apt for apt in appointments
        if apt["Date"] == tomorrow and apt["Status"] == "Booked"
    ]