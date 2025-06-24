import logging
from notion_client import Client
from datetime import datetime

# Load config
import json
with open("config.json") as f:
    config = json.load(f)

NOTION_TOKEN = config["notion_token"]
NOTION_DATABASE_ID = config["notion_database_id"]

notion = Client(auth=NOTION_TOKEN)

def create_task(task_name, due_date, assignee_email):
    try:
        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Task name": {"title": [{"text": {"content": task_name}}]},
                "Status": {"status": {"name": "Not started"}},
                "Due Date": {"date": {"start": due_date}},
                "Assignee": {"email": assignee_email}
            }
        )
        return "✅ Task created successfully."
    except Exception as e:
        return f"❌ Failed to create task: {str(e)}"

def get_tasks_for_assignee(email):
    try:
        result = notion.databases.query(
            **{
                "database_id": NOTION_DATABASE_ID,
                "filter": {
                    "property": "Assignee",
                    "email": {"equals": email}
                }
            }
        )
        tasks = result.get("results", [])
        if not tasks:
            return "📭 No tasks found for you."

        task_list = []
        for task in tasks:
            task_name = task["properties"]["Task name"]["title"][0]["text"]["content"]
            status = task["properties"]["Status"]["status"]["name"]
            due_date = task["properties"].get("Due Date", {}).get("date", {}).get("start", "No date")
            task_list.append(f"• {task_name} | Status: {status} | Due: {due_date}")

        return "\n".join(task_list)

    except Exception as e:
        return f"❌ Failed to fetch tasks: {str(e)}"

def get_task_details(task_name):
    try:
        result = notion.databases.query(
            **{
                "database_id": NOTION_DATABASE_ID,
                "filter": {
                    "property": "Task name",
                    "title": {"equals": task_name}
                }
            }
        )
        tasks = result.get("results", [])
        if not tasks:
            return f"No task found with name '{task_name}'."

        task = tasks[0]
        props = task["properties"]
        details = (
            f"📌 Task Name: {props['Task name']['title'][0]['text']['content']}\n"
            f"Status: {props['Status']['status']['name']}\n"
            f"Due Date: {props.get('Due Date', {}).get('date', {}).get('start', 'No date')}\n"
            f"Assignee: {props.get('Assignee', {}).get('email', 'Unassigned')}"
        )
        return details

    except Exception as e:
        return f"❌ Error fetching task details: {str(e)}"

def update_task_field(task_name, field, new_value):
    try:
        result = notion.databases.query(
            **{
                "database_id": NOTION_DATABASE_ID,
                "filter": {
                    "property": "Task name",
                    "title": {"equals": task_name}
                }
            }
        )
        tasks = result.get("results", [])
        if not tasks:
            return f"No task found with name '{task_name}'."

        page_id = tasks[0]["id"]
        update_payload = {}

        if field == "Task name":
            update_payload["Task name"] = {"title": [{"text": {"content": new_value}}]}
        elif field == "Status":
            update_payload["Status"] = {"status": {"name": new_value}}
        elif field == "Due Date":
            update_payload["Due Date"] = {"date": {"start": new_value}}
        elif field == "Assignee":
            update_payload["Assignee"] = {"email": new_value}
        else:
            return "Invalid field."

        notion.pages.update(page_id=page_id, properties=update_payload)
        return "✅ Task updated successfully."

    except Exception as e:
        return f"❌ Failed to update task: {str(e)}"
