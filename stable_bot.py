import os
import asyncio
from quart import Quart
import threading

# Initialize Quart app
webapp = Quart(__name__)

@webapp.route('/')
async def home():
    return "Benjamin is alive and healthy!"

# Function to run the web server
def run_webapp():
    # Port 7860 is mandatory for Hugging Face health checks
    webapp.run(host='0.0.0.0', port=7860)

# ... your existing environment variables and client setup ...


# Fix for Python 3.14 asyncio event loop issue (must be BEFORE pyrogram import)
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

if not BOT_TOKEN or not GROQ_KEY or not API_ID or not API_HASH:
    raise ValueError("Missing required environment variables")

# Groq client
client_groq = Groq(api_key=GROQ_KEY)

# Pyrogram bot
app = Client(
    "benjamin-bot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)

@app.on_message(filters.command("start"))
def start(_, message):
    message.reply_text("Holey cheese! I'm Benjamin 🐭\nReady for an adventure!")


@app.on_message(filters.text & ~filters.command(["start"]))
def reply(_, message):
    user_msg = message.text

    try:
        response = client_groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are Benjamin Stilton. Keep replies short, fun, and playful like a curious mouse."
                },
                {
                    "role": "user",
                    "content": user_msg
                }
            ]
        )

        reply_text = response.choices[0].message.content
        message.reply_text(reply_text)

    except Exception as e:
        print(f"Error: {e}")
        message.reply_text("Oops! Something went wrong 🧀")



# At the very bottom of your script, modify the startup:
if __name__ == "__main__":
    # Start the web server in a separate thread so it doesn't block the bot
    threading.Thread(target=run_webapp, daemon=True).start()
    
    # Now start your Pyrogram bot
    print("Benjamin is running...")
    app.run()