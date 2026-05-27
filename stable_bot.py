import os
import threading
from flask import Flask
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from groq import AsyncGroq

# Initialize Flask app for Hugging Face/Render health checks
webapp = Flask(__name__)

@webapp.route('/')
def home():
    return "AI Bot is alive and healthy!"

def run_webapp():
    # Mandatory port 7860 for Hugging Face spaces
    webapp.run(host='0.0.0.0', port=7860, debug=False, use_reloader=False)

# ENV variables
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

if not BOT_TOKEN or not GROQ_KEY or not API_ID or not API_HASH:
    raise ValueError("Missing required environment variables")

API_ID = int(API_ID)

# Initialize Async Clients
client_groq = AsyncGroq(api_key=GROQ_KEY)
app = Client(
    "ai-chatbot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)

@app.on_message(filters.text)
async def reply(client, message):
    user_msg = message.text
    bot_id = client.me.id
    bot_username = client.me.username.lower()

    is_private = message.chat.type == ChatType.PRIVATE
    is_reply = message.reply_to_message is not None
    is_reply_to_bot = is_reply and message.reply_to_message.from_user and message.reply_to_message.from_user.id == bot_id
    
    # Check if the bot's username is mentioned in the text (useful for groups)
    bot_mentioned = f"@{bot_username}" in user_msg.lower()

    # --- Smart Trigger Logic ---
    # 1. Always reply in Private Messages
    # 2. Reply in groups if someone explicitly replies to one of the bot's messages
    # 3. Reply in groups if someone tags the bot using @username
    should_respond = is_private or is_reply_to_bot or bot_mentioned

    if not should_respond:
        return

    try:
        # Clean up the message if the bot was tagged (removes the @username tag from the AI's prompt)
        clean_prompt = user_msg.replace(f"@{client.me.username}", "").strip()

        # Define your standard AI personality here
        system_prompt = (
            "You are a helpful, friendly, and intelligent AI assistant. "
            "Provide accurate, clear, and concise answers to the user's requests."
        )

        # Call Groq asynchronously using Llama 3.3
        response = await client_groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": clean_prompt}
            ]
        )

        reply_text = response.choices[0].message.content
        await message.reply_text(reply_text)

    except Exception as e:
        print(f"Error handling AI message: {e}")
        await message.reply_text("Sorry, I encountered an error while processing your request.")

if __name__ == "__main__":
    # Start the Flask web server in a separate thread for web service uptime tracking
    threading.Thread(target=run_webapp, daemon=True).start()
    
    print("AI Chatbot is running...")
    app.run()
