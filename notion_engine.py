import os
from notion_client import Client
from datetime import datetime
import json

# Load config
with open("config.json") as f:
    config = json.load(f)

notion = Client(auth=config["notion_token"])
DATABASE_ID = config["database_id"]

def create_task(task_name, due_date):
    try:
        new_task = {
            "Task name": {"title": [{"text": {"content": task_name}}]},
            "Status": {"select": {"name": "Not started"}},
            "Due date": {"date": {"start": datetime.strptime(due_date, "%m/%d/%Y").strftime("%Y-%m-%d")}},
        }

        notion.pages.create(parent={"database_id": DATABASE_ID}, properties=new_task)
        return f"✅ Task '{task_name}' created with due date {due_date}."
    except Exception as e:
        return f"❌ Failed to create task: {e}"

def list_tasks():
    try:
        results = notion.databases.query(database_id=DATABASE_ID).get("results")
        if not results:
            return "No tasks found."

        reply = "📋 Active Tasks:\n"
        for task in results:
            props = task["properties"]
            name = props.get("Task name", {}).get("title", [])
            task_name = name[0]["plain_text"] if name else "Unnamed"
            status = props.get("Status", {}).get("select", {}).get("name", "Unknown")
            reply += f"- {task_name} (Status: {status})\n"
        return reply

    except Exception as e:
        return f"❌ Failed to fetch tasks: {e}"

def update_task(task_name, prop, value):
    try:
        results = notion.databases.query(database_id=DATABASE_ID).get("results")
        matched_task = None
        for task in results:
            props = task["properties"]
            name = props.get("Task name", {}).get("title", [])
            if name and name[0]["plain_text"].lower() == task_name.lower():
                matched_task = task
                break

        if not matched_task:
            return f"❌ Task '{task_name}' not found."

        page_id = matched_task["id"]
        prop = prop.strip()
        update_data = {}
        db_props = matched_task["properties"]

        if prop not in db_props:
            return f"❌ Property '{prop}' does not exist."

        prop_type = db_props[prop]["type"]

        if prop_type == "select":
            update_data[prop] = {"select": {"name": value}}
        elif prop_type == "title":
            update_data[prop] = {"title": [{"text": {"content": value}}]}
        elif prop_type == "rich_text":
            update_data[prop] = {"rich_text": [{"text": {"content": value}}]}
        elif prop_type == "date":
            try:
                date_obj = datetime.strptime(value, "%m/%d/%Y")
                update_data[prop] = {"date": {"start": date_obj.strftime("%Y-%m-%d")}}
            except ValueError:
                return "❌ Invalid date format. Use MM/DD/YYYY."
        else:
            return f"❌ Property type '{prop_type}' not supported."

        notion.pages.update(page_id=page_id, properties=update_data)
        return f"✅ Updated '{prop}' of '{task_name}' to '{value}'."
    except Exception as e:
        return f"❌ Failed to update task: {e}"

def get_task_details(task_name):
    try:
        results = notion.databases.query(database_id=DATABASE_ID).get("results")
        matched_task = None
        for task in results:
            props = task["properties"]
            name = props.get("Task name", {}).get("title", [])
            if name and name[0]["plain_text"].lower() == task_name.lower():
                matched_task = task
                break

        if not matched_task:
            return f"❌ Task '{task_name}' not found."

        props = matched_task["properties"]
        details = f"📄 Task Details for '{task_name}':\n"
        for key, val in props.items():
            val_type = val["type"]
            display_val = "N/A"

            if val_type == "title":
                display_val = val["title"][0]["plain_text"] if val["title"] else "N/A"
            elif val_type == "select":
                display_val = val["select"]["name"] if val["select"] else "N/A"
            elif val_type == "rich_text":
                display_val = val["rich_text"][0]["plain_text"] if val["rich_text"] else "N/A"
            elif val_type == "date":
                display_val = val["date"]["start"] if val["date"] else "N/A"

            details += f"- {key}: {display_val}\n"
        return details

    except Exception as e:
        return f"❌ Failed to fetch task details: {e}"
