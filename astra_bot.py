import telebot
import json
import logging
from datetime import datetime, timedelta
from sarcasm_engine import get_sarcastic_reply, generate_sarcasm
import asyncio
import notion_engine

# Load config
with open("config.json") as f:
    config = json.load(f)

BOT_TOKEN = config["bot_token"]
bot = telebot.TeleBot(BOT_TOKEN)

LOG_FILE = "astra_log.json"
user_emails = {}
active_chats = set()

# Create one global event loop for async calls
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

def load_logs():
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_logs(logs):
    try:
        with open(LOG_FILE, "w") as f:
            json.dump(logs, f)
    except Exception as e:
        logging.error(f"Failed to save logs: {e}")

@bot.message_handler(commands=["start"])
def send_welcome(message):
    chat_id = message.chat.id
    active_chats.add(chat_id)
    bot.reply_to(message, f"🚀 Astra online for {message.from_user.first_name}! Type anything…")

@bot.message_handler(commands=["setemail"])
def set_email(message):
    chat_id = message.chat.id
    email = message.text.replace("/setemail", "").strip()
    if not email:
        bot.reply_to(message, "Send email like: /setemail you@example.com")
        return
    user_emails[str(chat_id)] = email
    bot.reply_to(message, f"✅ Email set as {email}")

@bot.message_handler(commands=["settask"])
def set_task(message):
    chat_id = message.chat.id
    if str(chat_id) not in user_emails:
        bot.reply_to(message, "Set your email first with /setemail")
        return

    parts = message.text.replace("/settask", "").strip().split("|")
    if len(parts) != 2:
        bot.reply_to(message, "Usage: /settask task name | MM/DD/YYYY")
        return
    task_name, due_date = parts
    email = user_emails[str(chat_id)]
    reply = notion_engine.create_task(task_name.strip(), due_date.strip(), email)
    bot.reply_to(message, reply)

@bot.message_handler(commands=["gettasks"])
def get_tasks(message):
    chat_id = message.chat.id
    if str(chat_id) not in user_emails:
        bot.reply_to(message, "Set your email first with /setemail")
        return
    email = user_emails[str(chat_id)]
    reply = notion_engine.list_tasks(email)
    bot.reply_to(message, reply)

@bot.message_handler(commands=["updatetask"])
def update_task(message):
    chat_id = message.chat.id
    parts = message.text.replace("/updatetask", "").strip().split("|")
    if len(parts) != 3:
        bot.reply_to(message, "Usage: /updatetask task_id | property | new_value")
        return
    task_id, prop, value = [x.strip() for x in parts]
    reply = notion_engine.update_task(task_id, prop, value)
    bot.reply_to(message, reply)

@bot.message_handler(commands=["taskdetails"])
def task_details(message):
    task_id = message.text.replace("/taskdetails", "").strip()
    if not task_id:
        bot.reply_to(message, "Usage: /taskdetails task_id")
        return
    reply = notion_engine.get_task_details(task_id)
    bot.reply_to(message, str(reply))

@bot.message_handler(commands=["help"])
def show_help(message):
    help_msg = (
        "📖 Available Commands:\n"
        "/start — Start the bot\n"
        "/setemail your@email.com — Set your assignee email\n"
        "/settask Task name | MM/DD/YYYY — Create a new task\n"
        "/gettasks — List your active tasks\n"
        "/updatetask task_id | property | new_value — Update a task\n"
        "/taskdetails task_id — Get task details\n"
        "/help — Show this help message"
    )
    bot.reply_to(message, help_msg)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    active_chats.add(chat_id)
    logs = load_logs()
    logs[str(chat_id)] = {"last_response": str(datetime.now())}
    save_logs(logs)

    user_message = message.text

    try:
        # Run sarcasm engine reply in global event loop
        response = loop.run_until_complete(get_sarcastic_reply(user_message))
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"🤖 Error: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("🚀 Astra is online.")
    bot.infinity_polling()
