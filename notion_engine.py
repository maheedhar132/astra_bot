import requests
import json
from datetime import datetime

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

def create_task(task_name, due_date):
    try:
        # Convert MM/DD/YYYY to ISO date
        due_date_iso = datetime.strptime(due_date, "%m/%d/%Y").date().isoformat()

        data = {
            "parent": {"database_id": DATABASE_ID},
            "properties": {
                "Task name": {"title": [{"text": {"content": task_name}}]},
                "Due date": {"date": {"start": due_date_iso}},
                "Status": {"select": {"name": "Not started"}}
            }
        }

        resp = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=data)
        resp.raise_for_status()
        return f"✅ Task '{task_name}' scheduled for {due_date}"
    except Exception as e:
        return f"❌ Failed to create task: {e}"

def list_tasks():
    try:
        payload = {
            "sorts": [{"property": "Due date", "direction": "ascending"}],
            "filter": {
                "property": "Status",
                "select": {"does_not_equal": "Done"}
            }
        }

        resp = requests.post(
            f"https://api.notion.com/v1/databases/{DATABASE_ID}/query",
            headers=HEADERS,
            json=payload
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])

        if not results:
            return "📝 No active tasks found."

        msg = "📋 Your tasks:\n"
        for page in results:
            pid = page["id"]
            props = page["properties"]
            name = props["Task name"]["title"][0]["plain_text"]
            due = props["Due date"]["date"]["start"]
            status = props["Status"]["select"]["name"]
            msg += f"- 🔹 {name} (Due: {due}, Status: {status}) [ID: {pid}]\n"
        return msg
    except requests.exceptions.RequestException as e:
        return f"❌ Failed to fetch tasks: {e}"
    except Exception as e:
        return f"❌ Failed during tasks handling: {e}"

def update_task(task_id, prop, value):
    try:
        prop_lower = prop.lower()
        if prop_lower == "status":
            prop_val = {"select": {"name": value}}
        elif prop_lower == "due date":
            iso_date = datetime.strptime(value, "%m/%d/%Y").date().isoformat()
            prop_val = {"date": {"start": iso_date}}
        elif prop_lower == "task name":
            prop_val = {"title": [{"text": {"content": value}}]}
        else:
            prop_val = {"rich_text": [{"text": {"content": value}}]}

        payload = {"properties": {prop: prop_val}}

        resp = requests.patch(
            f"https://api.notion.com/v1/pages/{task_id}",
            headers=HEADERS,
            json=payload
        )
        resp.raise_for_status()
        return f"✅ Updated '{prop}' to '{value}' for task {task_id}"
    except Exception as e:
        return f"❌ Failed to update task: {e}"

def get_task_details(task_id):
    try:
        resp = requests.get(f"https://api.notion.com/v1/pages/{task_id}", headers=HEADERS)
        resp.raise_for_status()
        page = resp.json()
        props = page["properties"]

        name = props["Task name"]["title"][0]["plain_text"]
        due = props["Due date"]["date"]["start"]
        status = props["Status"]["select"]["name"]

        return f"📝 {name}\n📅 Due: {due}\n🔖 Status: {status}"
    except Exception as e:
        return f"❌ Failed to fetch task details: {e}"
