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

# Notion Task Creation (with due date)
def create_notion_task(task_text, due_date):
    try:
        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Task name": {
                    "title": [{"text": {"content": task_text}}]
                },
                "Status": {
                    "status": {"name": "Not started"}
                },
                "Due date": {
                    "date": {"start": due_date}
                }
            }
        )
        return "✅ Task created successfully in Notion!"
    except Exception as e:
        return f"❌ Failed to create task: {str(e)}"

# Notion Task Listing (Not started)
def list_notion_tasks():
    try:
        result = notion.databases.query(
            **{
                "database_id": NOTION_DATABASE_ID,
                "filter": {
                    "property": "Status",
                    "status": {"equals": "Not started"}
                }
            }
        )
        tasks = result.get("results", [])
        if not tasks:
            return "No pending tasks 🚀"

        task_list = "\n".join(
            [f"• {task['properties']['Task name']['title'][0]['text']['content']}" for task in tasks]
        )
        return f"📋 Pending Tasks:\n{task_list}"
    except Exception as e:
        return f"Failed to fetch tasks: {str(e)}"

# Commands
@bot.message_handler(commands=["start"])
def send_welcome(message):
    chat_id = message.chat.id
    active_chats.add(chat_id)
    bot.reply_to(message, f"🚀 Astra online for {message.from_user.first_name}! Type anything…")

@bot.message_handler(commands=["settask"])
def set_task(message):
    task_text = message.text.replace("/settask", "").strip()
    if not task_text:
        bot.reply_to(message, "❗Give me the task text after /settask 📝")
        return
    bot.reply_to(message, "Please enter a due date in MM/DD/YYYY format:")

    # Set up a one-time next message handler for due date
    @bot.message_handler(func=lambda m: True)
    def get_due_date(m):
        try:
            due_date = datetime.strptime(m.text.strip(), "%m/%d/%Y").strftime("%Y-%m-%d")
            reply = create_notion_task(task_text, due_date)
            bot.reply_to(m, reply)
            bot.message_handler(func=lambda x: True)(handle_message)  # restore default handler
        except ValueError:
            bot.reply_to(m, "Invalid date format! Please use MM/DD/YYYY.")

@bot.message_handler(commands=["gettasks"])
def get_tasks(message):
    reply = list_notion_tasks()
    bot.reply_to(message, reply)

@bot.message_handler(commands=["help"])
def help_command(message):
    help_text = """
🛠️ *Astra Bot Commands*:
/start — Start Astra and activate session
/settask <task description> — Add a new task (will prompt for due date)
/gettasks — List all 'Not started' tasks from Notion
/help — Show this help message

Just type anything to get a sarcastic reply too 😎
"""
    bot.reply_to(message, help_text, parse_mode='Markdown')

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
