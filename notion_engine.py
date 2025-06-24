import requests
import json
from datetime import datetime

# Config constants
NOTION_TOKEN = "YOUR_NOTION_SECRET"
DATABASE_ID = "YOUR_DATABASE_ID"
NOTION_URL = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# In-memory cache for email -> user_id mapping
user_email_to_id = {}

def get_user_id_by_email(email):
    if email in user_email_to_id:
        return user_email_to_id[email]

    try:
        response = requests.get(f"{NOTION_URL}/users", headers=HEADERS)
        response.raise_for_status()
        users = response.json().get("results", [])

        for user in users:
            if user["type"] == "person" and user["person"].get("email") == email:
                user_id = user["id"]
                user_email_to_id[email] = user_id
                return user_id

        return None

    except Exception as e:
        print(f"❌ Error fetching users: {e}")
        return None


def create_task(task_name, due_date, assignee_email):
    try:
        user_id = get_user_id_by_email(assignee_email)
        if not user_id:
            return f"❌ Email not found in Notion users: {assignee_email}"

        payload = {
            "parent": {"database_id": DATABASE_ID},
            "properties": {
                "Task name": {"title": [{"text": {"content": task_name}}]},
                "Status": {"select": {"name": "Not started"}},
                "Due Date": {"date": {"start": due_date}},
                "Assignee": {"people": [{"id": user_id}]}
            }
        }

        response = requests.post(f"{NOTION_URL}/pages", headers=HEADERS, json=payload)
        response.raise_for_status()

        return f"✅ Task '{task_name}' created for {assignee_email}"

    except Exception as e:
        return f"❌ Failed to create task: {e}"


def list_tasks(assignee_email):
    try:
        user_id = get_user_id_by_email(assignee_email)
        if not user_id:
            return f"❌ Email not found in Notion users: {assignee_email}"

        filter_body = {
            "filter": {
                "and": [
                    {
                        "property": "Status",
                        "select": {"does_not_equal": "Done"}
                    },
                    {
                        "property": "Assignee",
                        "people": {"contains": user_id}
                    }
                ]
            }
        }

        response = requests.post(f"{NOTION_URL}/databases/{DATABASE_ID}/query", headers=HEADERS, json=filter_body)
        response.raise_for_status()
        data = response.json()

        tasks = data.get("results", [])
        if not tasks:
            return "📭 No active tasks found."

        msg = "📋 Active Tasks:\n"
        for task in tasks:
            name = task["properties"]["Task name"]["title"][0]["plain_text"]
            due_date = task["properties"]["Due Date"]["date"]["start"]
            task_id = task["id"]
            msg += f"• `{task_id}` — {name} (Due: {due_date})\n"

        return msg

    except Exception as e:
        return f"❌ Failed to fetch tasks: {e}"


def update_task(task_id, prop, value):
    try:
        payload = {"properties": {}}
        if prop.lower() == "status":
            payload["properties"]["Status"] = {"select": {"name": value}}
        elif prop.lower() == "due date":
            payload["properties"]["Due Date"] = {"date": {"start": value}}
        else:
            return "❌ Only 'Status' and 'Due Date' can be updated."

        response = requests.patch(f"{NOTION_URL}/pages/{task_id}", headers=HEADERS, json=payload)
        response.raise_for_status()

        return f"✅ Task {task_id} updated."

    except Exception as e:
        return f"❌ Failed to update task: {e}"


def get_task_details(task_id):
    try:
        response = requests.get(f"{NOTION_URL}/pages/{task_id}", headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        task_name = data["properties"]["Task name"]["title"][0]["plain_text"]
        due_date = data["properties"]["Due Date"]["date"]["start"]
        status = data["properties"]["Status"]["select"]["name"]

        return f"📖 *Task:* {task_name}\n📅 *Due:* {due_date}\n📌 *Status:* {status}"

    except Exception as e:
        return f"❌ Failed to fetch task details: {e}"
