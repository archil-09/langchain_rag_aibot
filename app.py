"""
app.py — Main Flask webhook
Ties together RAG, appointments, reminders and WhatsApp
"""

from flask import Flask, request, jsonify
from dotenv import load_dotenv
from src.rag import load_documents, ask_rag, detect_intent
from src.appointment import (
    book_appointment,
    reschedule_appointment,
    cancel_appointment,
    get_appointment,
    init_appointments_file,
    validate_date,
    validate_time

)
from src.whatsapp import send_message
from src.reminder import start_reminder_scheduler
import os

load_dotenv()

app = Flask(__name__)

# ── Load documents at startup ───────────────────────────────────────
FILE_PATH = "data/Dental_Clinic_RAG_Documents.docx"
retriever = load_documents(FILE_PATH)
init_appointments_file()
start_reminder_scheduler()

# ── Conversation memory ─────────────────────────────────────────────
user_sessions = {}
processed_messages = set()

def handle_booking_flow(phone: str, message: str) -> str:
    """Multi-step conversation flow for booking an appointment"""
    session = user_sessions.get(phone, {})
    step = session.get("step", "get_name")
    data = session.get("data", {})

    if step == "get_name":
        data["name"] = message.strip()
        user_sessions[phone] = {"flow": "booking", "step": "get_treatment", "data": data}
        return (
            f"Nice to meet you, {data['name']}! 😊\n\n"
            f"What treatment are you looking for?\n"
            f"(e.g. Root Canal, Teeth Whitening, Braces, Cleaning, Extraction)"
        )

    elif step == "get_treatment":
        data["treatment"] = message.strip()
        user_sessions[phone] = {"flow": "booking", "step": "get_date", "data": data}
        return (
            f"Great choice! 🦷\n\n"
            f"What date would you prefer?\n"
            f"Please enter in format: YYYY-MM-DD\n"
            f"Example: 2026-06-20"
        )

    elif step == "get_date":
        if not validate_date(message.strip()):
            return (
                "❌ That doesn't look like a valid date.\n"
                "Please enter in format: YYYY-MM-DD\n"
                "Example: 2026-06-20"
            )
        data["date"] = message.strip()
        user_sessions[phone] = {"flow": "booking", "step": "get_time", "data": data}
        return (
            f"Perfect! What time works for you?\n"
            f"Please enter in format: HH:MM AM/PM\n"
            f"Example: 10:30 AM"
        )

    elif step == "get_time":
        if not validate_time(message.strip()):
            return (
                "❌ That doesn't look like a valid time.\n"
                "Please enter in format: HH:MM AM/PM\n"
                "Example: 3:00 PM"
            )
        data["time"] = message.strip()
        result = book_appointment(
            name=data["name"],
            phone=phone,
            treatment=data["treatment"],
            date=data["date"],
            time=data["time"]
        )
        user_sessions.pop(phone, None)
        return result

    return "Something went wrong. Please type 'book' to start again."


def handle_reschedule_flow(phone: str, message: str) -> str:
    """Multi-step flow for rescheduling"""
    session = user_sessions.get(phone, {})
    step = session.get("step", "get_new_date")
    data = session.get("data", {})

    if step == "get_new_date":
        data["new_date"] = message.strip()
        user_sessions[phone] = {"flow": "rescheduling", "step": "get_new_time", "data": data}
        return (
            "What time would you like?\n"
            "Please enter in format: HH:MM AM/PM\n"
            "Example: 2:30 PM"
        )

    elif step == "get_new_time":
        data["new_time"] = message.strip()
        result = reschedule_appointment(
            phone=phone,
            new_date=data["new_date"],
            new_time=data["new_time"]
        )
        user_sessions.pop(phone, None)
        return result

    return "Something went wrong. Please type 'reschedule' to start again."


def process_message(phone: str, message: str) -> str:
    """Main message router — detects intent and handles accordingly"""
    message_lower = message.lower().strip()
    greetings = ["hi", "hii", "hello", "hey", "heya", "hii!", "hi!", "namaste"]
    if message_lower in greetings:
        if phone not in user_sessions:
            return (
                "👋 Hello! Welcome to our dental clinic.\n\n"
                "I can help you:\n"
                "📅 Book an appointment\n"
                "🔄 Reschedule or cancel\n"
                "❓ Answer questions about treatments\n\n"
                "How can I help you today?"
            )

    # If user is mid-conversation handle it first


    # If user is mid-conversation handle it first
    if phone in user_sessions:
        session = user_sessions[phone]
        flow = session.get("flow")

        if flow == "booking":
            return handle_booking_flow(phone, message)
        elif flow == "rescheduling":
            return handle_reschedule_flow(phone, message)

    # Handle yes response to start booking
    if message_lower in ["yes", "yeah", "sure", "ok", "okay", "haan", "ha", "y"]:
        user_sessions[phone] = {"flow": "booking", "step": "get_name", "data": {}}
        return (
            "I'd love to help you book an appointment! 😊\n\n"
            "First, what's your full name?"
        )

    # Detect intent for new messages
    intent = detect_intent(message)

    if intent == "book":
        user_sessions[phone] = {"flow": "booking", "step": "get_name", "data": {}}
        return (
            "I'd love to help you book an appointment! 😊\n\n"
            "First, what's your full name?"
        )

    elif intent == "reschedule":
        existing = get_appointment(phone)
        if "couldn't find" in existing:
            return existing
        user_sessions[phone] = {"flow": "rescheduling", "step": "get_new_date", "data": {}}
        return (
            f"{existing}\n\n"
            f"What's your new preferred date?\n"
            f"Format: YYYY-MM-DD (e.g. 2026-06-25)"
        )

    elif intent == "cancel":
        return cancel_appointment(phone)

    elif intent == "status":
        return get_appointment(phone)

    else:
        return ask_rag(retriever, message)


# ── Webhook verification ────────────────────────────────────────────
@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == os.getenv("VERIFY_TOKEN"):
        return request.args.get("hub.challenge")
    return "Invalid token", 403


# ── Webhook receiver ────────────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        message_id = message["id"]

        # Ignore duplicate messages
        if message_id in processed_messages:
            return jsonify({"status": "ok"})
        processed_messages.add(message_id)

        phone = message["from"]
        text = message["text"]["body"]
        print(f"Message from {phone}: {text}")

        reply = process_message(phone, text)
        send_message(phone, reply)

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

    return jsonify({"status": "ok"})


# ── Health check ────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "DentBot is running! 🦷"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)