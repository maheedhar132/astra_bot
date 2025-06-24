import requests
import json
from datetime import datetime
from configparser import ConfigParser

# Load config
with open("config.json") as f:
    config = json.load(f)

NOTION_TOKEN = config["notion_token"]
DATABASE_ID = config["notion_database_id"]

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}


def create_task(task_name, due_date, assignee_email):
    try:
        # Convert to ISO date format
        due_date_obj = datetime.strptime(due_date, "%m/%d/%Y")
        due_date_iso = due_date_obj.date().isoformat()

        data = {
            "parent": {"database_id": DATABASE_ID},
            "properties": {
                "Task name": {"title": [{"text": {"content": task_name}}]},
                "Due date": {"date": {"start": due_date_iso}},
                "Assignee": {"rich_text": [{"text": {"content": assignee_email}}]},
                "Status": {"select": {"name": "Not started"}}
            }
        }

        response = requests.post(
            "https://api.notion.com/v1/pages", headers=HEADERS, json=data
        )
        response.raise_for_status()
        return f"✅ Task '{task_name}' created for {due_date}"

    except Exception as e:
        return f"❌ Failed to create task: {e}"


def list_tasks(assignee_email):
    try:
        payload = {
            "filter": {
                "and": [
                    {
                        "property": "Assignee",
                        "rich_text": {
                            "equals": assignee_email
                        }
                    },
                    {
                        "property": "Status",
                        "select": {"does_not_equal": "Done"}
                    }
                ]
            },
            "sorts": [{"property": "Due date", "direction": "ascending"}]
        }

        response = requests.post(
            f"https://api.notion.com/v1/databases/{DATABASE_ID}/query",
            headers=HEADERS,
            json=payload
        )
        response.raise_for_status()
        results = response.json().get("results")

        if not results:
            return "📭 No active tasks found."

        reply = "📋 Your tasks:\n"
        for page in results:
            props = page["properties"]
            reply += (
                f"\n🆔 {page['id']}\n"
                f"📝 {props['Task name']['title'][0]['text']['content']}\n"
                f"📅 {props['Due date'].get('date', {}).get('start', 'No date')}\n"
                f"🔖 {props['Status']['select']['name']}\n"
            )
        return reply

    except Exception as e:
        return f"❌ Failed to fetch tasks: {e}"


def update_task(task_id, prop, value):
    try:
        if prop.lower() == "status":
            prop_data = {"select": {"name": value}}
        elif prop.lower() == "due date":
            due_date_obj = datetime.strptime(value, "%m/%d/%Y")
            prop_data = {"date": {"start": due_date_obj.date().isoformat()}}
        elif prop.lower() == "task name":
            prop_data = {"title": [{"text": {"content": value}}]}
        else:
            prop_data = {"rich_text": [{"text": {"content": value}}]}

        payload = {
            "properties": {
                prop: prop_data
            }
        }

        response = requests.patch(
            f"https://api.notion.com/v1/pages/{task_id}",
            headers=HEADERS,
            json=payload
        )
        response.raise_for_status()
        return f"✅ Updated {prop} to {value}"

    except Exception as e:
        return f"❌ Failed to update task: {e}"


def get_task_details(task_id):
    try:
        response = requests.get(
            f"https://api.notion.com/v1/pages/{task_id}",
            headers=HEADERS
        )
        response.raise_for_status()
        page = response.json()
        props = page["properties"]

        details = (
            f"📝 {props['Task name']['title'][0]['text']['content']}\n"
            f"📅 {props['Due date'].get('date', {}).get('start', 'No date')}\n"
            f"👤 {props['Assignee']['rich_text'][0]['text']['content']}\n"
            f"🔖 {props['Status']['select']['name']}"
        )
        return details

    except Exception as e:
        return f"❌ Failed to fetch task details: {e}"
