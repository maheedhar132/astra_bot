from notion_client import Client
from datetime import datetime
import logging
import json

with open("config.json") as f:
    config = json.load(f)

NOTION_TOKEN = config["notion_token"]
NOTION_DATABASE_ID = config["notion_database_id"]

notion = Client(auth=NOTION_TOKEN)

def create_task(task_name, due_date):
    try:
        iso_date = datetime.strptime(due_date, "%m/%d/%Y").date().isoformat()

        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Task name": {"title": [{"text": {"content": task_name}}]},
                "Status": {"status": {"name": "Not started"}},
                "Due Date": {"date": {"start": iso_date}},
            }
        )
        return "✅ Task created successfully in Notion!"
    except Exception as e:
        logging.error(f"Task creation error: {e}")
        return f"❌ Failed to create task: {str(e)}"

def list_tasks():
    try:
        result = notion.databases.query(
            database_id=NOTION_DATABASE_ID,
            filter={"property": "Status", "status": {"does_not_equal": "Done"}}
        )
        tasks = result.get("results", [])
        if not tasks:
            return "🎉 No active tasks found."

        task_list = ""
        for task in tasks:
            props = task["properties"]
            name = props["Task name"]["title"][0]["text"]["content"]
            status = props["Status"]["status"]["name"]
            due_date = props.get("Due Date", {}).get("date", {}).get("start", "N/A")
            task_list += f"• {name} | Status: {status} | Due: {due_date}\n"

        return f"📋 Active Tasks:\n{task_list}"

    except Exception as e:
        logging.error(f"Task listing error: {e}")
        return f"❌ Failed to fetch tasks: {str(e)}"

def get_task_page_by_name(task_name):
    result = notion.databases.query(
        database_id=NOTION_DATABASE_ID,
        filter={"property": "Task name", "title": {"equals": task_name}}
    )
    tasks = result.get("results", [])
    return tasks[0] if tasks else None

def update_task(task_name, property_name, new_value):
    try:
        task_page = get_task_page_by_name(task_name)
        if not task_page:
            return f"❌ Task '{task_name}' not found."

        task_id = task_page["id"]
        prop_update = {}

        if property_name == "Task name":
            prop_update["Task name"] = {"title": [{"text": {"content": new_value}}]}
        elif property_name == "Status":
            prop_update["Status"] = {"status": {"name": new_value}}
        elif property_name == "Due Date":
            iso_date = datetime.strptime(new_value, "%m/%d/%Y").date().isoformat()
            prop_update["Due Date"] = {"date": {"start": iso_date}}
        elif property_name == "Description":
            prop_update["Description"] = {"rich_text": [{"text": {"content": new_value}}]}
        elif property_name == "Priority":
            prop_update["Priority"] = {"select": {"name": new_value}}
        elif property_name == "Task Type":
            prop_update["Task Type"] = {"select": {"name": new_value}}
        else:
            return f"❌ Unsupported property: {property_name}"

        notion.pages.update(page_id=task_id, properties=prop_update)
        return "✅ Task updated successfully."

    except Exception as e:
        logging.error(f"Task update error: {e}")
        return f"❌ Failed to update task: {str(e)}"

def get_task_details(task_name):
    try:
        task_page = get_task_page_by_name(task_name)
        if not task_page:
            return f"❌ Task '{task_name}' not found."

        props = task_page["properties"]
        details = {
            "Task name": props["Task name"]["title"][0]["text"]["content"],
            "Status": props["Status"]["status"]["name"],
            "Due Date": props.get("Due Date", {}).get("date", {}).get("start", "N/A"),
            "Description": props.get("Description", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "N/A"),
            "Priority": props.get("Priority", {}).get("select", {}).get("name", "N/A"),
            "Task Type": props.get("Task Type", {}).get("select", {}).get("name", "N/A"),
        }

        return json.dumps(details, indent=2)

    except Exception as e:
        logging.error(f"Task detail fetch error: {e}")
        return f"❌ Failed to fetch details: {str(e)}"
