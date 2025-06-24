import telebot
import json
import logging
from datetime import datetime, timedelta
from sarcasm_engine import get_sarcastic_reply

# Load config
with open("config.json") as f:
    config = json.load(f)

BOT_TOKEN = config["bot_token"]
bot = telebot.TeleBot(BOT_TOKEN)

# Log file
LOG_FILE = "astra_log.json"

# In-memory active chats
active_chats = set()

def load_logs():
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_logs(logs):
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f)

@bot.message_handler(commands=["start"])
def send_welcome(message):
    chat_id = message.chat.id
    active_chats.add(chat_id)
    bot.reply_to(message, f"🚀 Astra online for {message.from_user.first_name}! Type anything…")

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
            last_time = datetime.strptime(last_response_time, "%Y-%m-%d %H:%M:%S.%f")
            if datetime.now() - last_time > timedelta(hours=1):
                sarcasm = get_sarcastic_reply("No response for an hour, roast them.")
                bot.send_message(chat_id, sarcasm)

        check_msg = "Yo, did you do anything productive yet? 👀"
        bot.send_message(chat_id, check_msg)
        logs[str(chat_id)] = {"last_check": str(datetime.now())}

    save_logs(logs)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("🚀 Astra is online.")
    bot.infinity_polling()
