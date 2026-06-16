"""
whatsapp.py — Handles all WhatsApp message sending via Meta API
"""

import os
import requests


def send_message(to: str, message: str) -> bool:
    """Send a WhatsApp text message to a phone number"""
    phone_number_id = os.getenv("PHONE_NUMBER_ID")
    token = os.getenv("ACCESS_TOKEN")

    print(f"Sending to: {to}")
    print(f"Phone Number ID: {phone_number_id}")
    print(f"Token starts with: {token[:10] if token else 'MISSING'}")

    url = f"https://graph.facebook.com/v25.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }

    response = requests.post(url, headers=headers, json=payload)
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")

    if response.status_code == 200:
        return True
    else:
        print(f"Failed to send message: {response.text}")
        return False

def send_reminder(to: str, name: str, treatment: str, date: str, time: str):
    """Send appointment reminder message"""
    message = (
        f"👋 Hello {name}!\n\n"
        f"This is a reminder from your dental clinic.\n\n"
        f"🦷 Treatment: {treatment}\n"
        f"📅 Date: {date} (Tomorrow)\n"
        f"⏰ Time: {time}\n\n"
        f"Please arrive 10 minutes early.\n"
        f"To reschedule, reply to this message anytime!"
    )
    return send_message(to, message)