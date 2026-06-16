"""
reminder.py — Sends automatic appointment reminders every day at 9am
"""

import schedule
import time
import threading
from src.appointment import get_tomorrows_appointments
from src.whatsapp import send_reminder


def send_daily_reminders():
    """Check tomorrow's appointments and send reminders"""
    print("Checking tomorrow's appointments for reminders...")
    appointments = get_tomorrows_appointments()

    if not appointments:
        print("No appointments tomorrow.")
        return

    for apt in appointments:
        send_reminder(
            to=apt["Phone"],
            name=apt["Name"],
            treatment=apt["Treatment"],
            date=apt["Date"],
            time=apt["Time"]
        )
        print(f"Reminder sent to {apt['Name']} ({apt['Phone']})")


def start_reminder_scheduler():
    """Start the reminder scheduler in a background thread"""

    # Send reminders every day at 9:00 AM
    schedule.every().day.at("09:00").do(send_daily_reminders)

    def run_scheduler():
        print("Reminder scheduler started — reminders will be sent daily at 9:00 AM")
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    # Run in background so it doesn't block Flask
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()