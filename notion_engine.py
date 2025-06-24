import requests
import json
from datetime import datetime

# Load config
with open("config.json") as f:
    config = json.load(f)

NOTION_URL = "https://api.notion.com/v1"
DATABASE_ID = config["notion_database_id"]
HEADERS = {
    "Authorization": f"Bearer {config['notion_token']}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def create_task(task_name, due_date, email):
    try:
        task_payload = {
            "parent": {"database_id": DATABASE_ID},
            "properties": {
                "Task name": {
                    "title": [
                        {
                            "text": {
                                "content": task_name
                            }
                        }
                    ]
                },
                "Due Date": {
                    "date": {
                        "start": datetime.strptime(due_date, "%m/%d/%Y").isoformat()
                    }
                },
                "Status": {
                    "select": {
                        "name": "Not started"
                    }
                },
                "Assignee": {
                    "people": []
                }
            }
        }

        response = requests.post(f"{NOTION_URL}/pages", headers=HEADERS, json=task_payload)
        response.raise_for_status()
        return f"✅ Task '{task_name}' added with due date {due_date}."

    except Exception as e:
        return f"❌ Failed to add task: {e}"

def list_tasks(email):
    try:
        filter_body = {
            "filter": {
                "property": "Assignee",
                "people": {
                    "contains": email
                }
            }
        }
        response = requests.post(f"{NOTION_URL}/databases/{DATABASE_ID}/query", headers=HEADERS, json=filter_body)
        response.raise_for_status()
        data = response.json()
        tasks = data.get("results", [])

        if not tasks:
            return "No tasks found for you. Try adding some, you slacker."

        msg = "📋 Your Tasks:\n"
        for task in tasks:
            name = task["properties"]["Task name"]["title"][0]["plain_text"]
            due_date = task["properties"]["Due Date"]["date"]["start"]
            msg += f"• {name} — Due: {due_date}\n"

        return msg

    except Exception as e:
        return f"❌ Failed to fetch tasks: {e}"

def update_task(task_id, property_name, new_value):
    try:
        update_payload = {
            "properties": {
                property_name: {
                    "rich_text": [
                        {
                            "text": {
                                "content": new_value
                            }
                        }
                    ]
                }
            }
        }

        response = requests.patch(f"{NOTION_URL}/pages/{task_id}", headers=HEADERS, json=update_payload)
        response.raise_for_status()
        return f"✅ Task {task_id} updated: {property_name} → {new_value}"

    except Exception as e:
        return f"❌ Failed to update task: {e}"

def get_task_details(task_id):
    try:
        response = requests.get(f"{NOTION_URL}/pages/{task_id}", headers=HEADERS)
        response.raise_for_status()
        task = response.json()

        name = task["properties"]["Task name"]["title"][0]["plain_text"]
        due_date = task["properties"]["Due Date"]["date"]["start"]
        status = task["properties"]["Status"]["select"]["name"]

        details = f"📌 Task Details:\nName: {name}\nDue Date: {due_date}\nStatus: {status}"
        return details

    except Exception as e:
        return f"❌ Failed to get task details: {e}"
