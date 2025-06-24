import telebot
import json
import logging
from datetime import datetime, timedelta
from sarcasm_engine import get_sarcastic_reply, generate_sarcasm
from notion_client import Client

# Load config
with open("config.json") as f:
    config = json.load(f)

BOT_TOKEN = config["bot_token"]
NOTION_TOKEN = config["notion_token"]
NOTION_DATABASE_ID = config["notion_database_id"]

bot = telebot.TeleBot(BOT_TOKEN)
notion = Client(auth=NOTION_TOKEN)

LOG_FILE = "astra_log.json"
active_chats = set()

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

# Notion Task Creation
def create_notion_task(task_text):
    try:
        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Name": {
                    "title": [
                        {"text": {"content": task_text}}
                    ]
                },
                "Status": {
                    "select": {"name": "Pending"}
                }
            }
        )
        return "Task created successfully in Notion ✅"
    except Exception as e:
        return f"Failed to create task: {str(e)}"

# Notion Task Listing
def list_notion_tasks():
    try:
        result = notion.databases.query(
            **{
                "database_id": NOTION_DATABASE_ID,
                "filter": {
                    "property": "Status",
                    "select": {"equals": "Pending"}
                }
            }
        )
        tasks = result.get("results", [])
        if not tasks:
            return "No pending tasks 🚀"

        task_list = "\n".join(
            [f"• {task['properties']['Name']['title'][0]['text']['content']}" for task in tasks]
        )
        return f"📋 Pending Tasks:\n{task_list}"
    except Exception as e:
        return f"Failed to fetch tasks: {str(e)}"

@bot.message_handler(commands=["start"])
def send_welcome(message):
    chat_id = message.chat.id
    active_chats.add(chat_id)
    bot.reply_to(message, f"🚀 Astra online for {message.from_user.first_name}! Type anything…")

@bot.message_handler(commands=["settask"])
def set_task(message):
    task_text = message.text.replace("/settask", "").strip()
    if not task_text:
        bot.reply_to(message, "Give me the task text after /settask 📝")
        return
    reply = create_notion_task(task_text)
    bot.reply_to(message, reply)

@bot.message_handler(commands=["gettasks"])
def get_tasks(message):
    reply = list_notion_tasks()
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
