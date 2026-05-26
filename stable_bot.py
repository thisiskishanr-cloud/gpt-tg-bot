import os
import asyncio
import threading
import requests  # Added for fetching the GitHub list
from flask import Flask
from pyrogram.enums import ChatType


# Initialize Flask app
webapp = Flask(__name__)

@webapp.route('/')
def home():
    return "Benjamin is alive and healthy!"

def run_webapp():
    # Mandatory port 7860 for Hugging Face health checks
    webapp.run(host='0.0.0.0', port=7860, debug=False, use_reloader=False)

# Fix for Python 3.14 asyncio event loop issue
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from pyrogram import Client, filters
from groq import Groq

# ENV variables
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
# Update this with your actual Raw GitHub URL
MANUAL_LIST_URL = "https://raw.githubusercontent.com/thisiskishanr-cloud/benjamin-bot/refs/heads/main/manual_books.txt"

if not BOT_TOKEN or not GROQ_KEY or not API_ID or not API_HASH:
    raise ValueError("Missing required environment variables")

client_groq = Groq(api_key=GROQ_KEY)

app = Client(
    "benjamin-bot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)

def get_manual_list():
    """Fetches standalone titles from GitHub to keep Benjamin's memory updated."""
    try:
        r = requests.get(MANUAL_LIST_URL, timeout=5)
        return r.text.replace('\n', ', ')
    except Exception as e:
        print(f"List Fetch Error: {e}")
        return "None currently listed."

@app.on_message(filters.command("start"))
def start(_, message):
    message.reply_text("Holey cheese! I'm Benjamin 🐭\nHow can I help your whiskers today?")

@app.on_message(filters.text & ~filters.command(["start"]))
def reply(client, message):
    user_msg = message.text
    words = user_msg.split()
    bot_id = client.me.id

    is_private = message.chat.type == ChatType.PRIVATE
    is_reply = message.reply_to_message is not None
    is_reply_to_bot = is_reply and message.reply_to_message.from_user and message.reply_to_message.from_user.id == bot_id
    name_mentioned = "benjamin" in user_msg.lower()

    # 2. The Gatekeeper
    if not is_private and is_reply and not is_reply_to_bot:
        return

    # 3. The Trigger
    if not (is_private or is_reply_to_bot or len(words) >= 3 or (len(words) < 3 and name_mentioned)):
        return

    try:
        standalone_titles = get_manual_list()

        # --- GROUP PROMPT ---
        group_prompt = f"""
You are Benjamin Stilton 🐭, a playful mouse in the Geronimo Stilton Support Group! 
Every user prompt is a live Telegram message you must react to.
COMPLETED SERIES:
1. GS Main (1-83), Kingdom of Fantasy (1-15), Journey Through Time (1-8), Thea Specials.
2. Mini-Series: Cavemice (1-15), Spacemice (1-12), Creepella (1-9).
3. Others: {standalone_titles}
LIBRARIAN RULES:
- Confirm available books are in the channel; else say it will be uploaded shortly.
- SECURITY: If a message is a scam (money, paid work, adult content), playfully reject it and include #report @admin.
- Be fun, mousy, and keep replies short.
- Never ask follow-up questions; provide the answer and stop; never tell anything you aren't sure of."""

        # --- PM PROMPT ---
        pm_prompt = f"""
You are Benjamin Stilton 🐭! You’re moderator of @geronimostiltonbooks group.
But now you’re in a private message (PM) with a friend. Answer cheerfully for everything and never ask follow up questions. Give the response and stop. Make the response short."""

        # 4. Selection
        system_content = pm_prompt if is_private else group_prompt

        # ... Proceed to Groq API call ...

        response = client_groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_msg}
            ]
        )

        reply_text = response.choices[0].message.content
        message.reply_text(reply_text)

    except Exception as e:
        print(f"Error: {e}")
        # Keep the error message in character
        message.reply_text("Oops! My whiskers got tangled. Something went wrong! 🧀")

if __name__ == "__main__":
    # Start the Flask web server in a separate thread to satisfy HF health checks
    threading.Thread(target=run_webapp, daemon=True).start()
    
    print("Benjamin is running...")
    app.run()
