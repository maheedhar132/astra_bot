import telebot
import json
import logging
from datetime import datetime, timedelta
from sarcasm_engine import get_sarcastic_reply, generate_sarcasm
import notion_engine

# Load config
with open("config.json") as f:
    config = json.load(f)

BOT_TOKEN = config["bot_token"]

bot = telebot.TeleBot(BOT_TOKEN)
LOG_FILE = "astra_log.json"
active_chats = set()

user_emails = {}

def load_logs():
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except Exception:
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
    bot.reply_to(message, f"🚀 Astra online for {message.from_user.first_name}! Type /help for commands.")

@bot.message_handler(commands=["help"])
def show_help(message):
    help_text = """
📌 Available Commands:
/start — Activate Astra
/set_email your@email.com — Set your Notion email
/settask Task text | MM/DD/YYYY — Create a new task
/gettasks — List your tasks
/task_details Task Name — Get full details
/update_task Task Name | Field | New Value — Update a task field
/help — Show this help message
"""
    bot.reply_to(message, help_text)

@bot.message_handler(commands=["set_email"])
def set_email(message):
    email = message.text.replace("/set_email", "").strip()
    if not email:
        bot.reply_to(message, "Please provide your email.")
        return
    user_emails[message.chat.id] = email
    bot.reply_to(message, f"✅ Email set as {email}.")

@bot.message_handler(commands=["settask"])
def set_task(message):
    if message.chat.id not in user_emails:
        bot.reply_to(message, "Set your email first with /set_email.")
        return
    parts = message.text.replace("/settask", "").strip().split("|")
    if len(parts) != 2:
        bot.reply_to(message, "Use format: /settask Task text | MM/DD/YYYY")
        return
    task_text, due_date = parts
    reply = notion_engine.create_task(task_text.strip(), due_date.strip(), user_emails[message.chat.id])
    bot.reply_to(message, reply)

@bot.message_handler(commands=["gettasks"])
def get_tasks(message):
    if message.chat.id not in user_emails:
        bot.reply_to(message, "Set your email first with /set_email.")
        return
    reply = notion_engine.get_tasks_for_assignee(user_emails[message.chat.id])
    bot.reply_to(message, reply)

@bot.message_handler(commands=["task_details"])
def task_details(message):
    task_name = message.text.replace("/task_details", "").strip()
    if not task_name:
        bot.reply_to(message, "Provide the task name.")
        return
    reply = notion_engine.get_task_details(task_name)
    bot.reply_to(message, reply)

@bot.message_handler(commands=["update_task"])
def update_task(message):
    parts = message.text.replace("/update_task", "").strip().split("|")
    if len(parts) != 3:
        bot.reply_to(message, "Use format: /update_task Task name | Field | New Value")
        return
    task_name, field, new_value = [p.strip() for p in parts]
    reply = notion_engine.update_task_field(task_name, field, new_value)
    bot.reply_to(message, reply)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    active_chats.add(chat_id)
    logs = load_logs()
    logs[str(chat_id)] = {"last_response": str(datetime.now())}
    save_logs(logs)
    user_message = message.text
    response = get_sarcastic_reply(user_message)
    bot.reply_to(message, response)

def send_productivity_check():
    logs = load_logs()
    for chat_id in active_chats:
        last_response_time = logs.get(str(chat_id), {}).get("last_response")
        if last_response_time:
            try:
                last_time = datetime.strptime(last_response_time, "%Y-%m-%d %H:%M:%S.%f")
                if datetime.now() - last_time > timedelta(hours=1):
                    sarcasm = generate_sarcasm("no_response")
                    bot.send_message(chat_id, sarcasm)
            except Exception as e:
                logging.error(f"Time parsing issue: {e}")
        check_msg = "Yo, did you do anything productive yet? 👀"
        bot.send_message(chat_id, check_msg)
        logs[str(chat_id)] = {"last_check": str(datetime.now())}
    save_logs(logs)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("🚀 Astra is online.")
    bot.infinity_polling()
