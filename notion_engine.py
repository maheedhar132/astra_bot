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
                "Due Date": {"date": {"start": iso_date}}
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
            filter={
                "property": "Status",
                "status": {"does_not_equal": "Done"}
            }
        )
        tasks = result.get("results", [])
        if not tasks:
            return "🎉 No active tasks found."

        task_list = ""
        for task in tasks:
            properties = task["properties"]
            name = properties["Task name"]["title"][0]["text"]["content"] if properties["Task name"]["title"] else "Untitled"
            status = properties["Status"]["status"]["name"]
            due_date = properties.get("Due Date", {}).get("date", {}).get("start", "N/A")
            task_list += f"• {name} | Status: {status} | Due: {due_date}\n"

        return f"📋 Active Tasks:\n{task_list}"

    except Exception as e:
        logging.error(f"Task listing error: {e}")
        return f"❌ Failed to fetch tasks: {str(e)}"


def update_task(task_id, property_name, new_value):
    try:
        prop_update = {}

        if property_name == "Task name":
            prop_update["Task name"] = {"title": [{"text": {"content": new_value}}]}
        elif property_name == "Status":
            prop_update["Status"] = {"status": {"name": new_value}}
        elif property_name == "Due Date":
            iso_date = datetime.strptime(new_value, "%m/%d/%Y").date().isoformat()
            prop_update["Due Date"] = {"date": {"start": iso_date}}
        else:
            return f"❌ Unsupported property: {property_name}"

        notion.pages.update(page_id=task_id, properties=prop_update)
        return "✅ Task updated successfully."

    except Exception as e:
        logging.error(f"Task update error: {e}")
        return f"❌ Failed to update task: {str(e)}"


def get_task_details(task_id):
    try:
        task = notion.pages.retrieve(page_id=task_id)
        properties = task["properties"]
        details = {}

        for key, prop in properties.items():
            if prop["type"] == "title":
                details[key] = prop["title"][0]["text"]["content"] if prop["title"] else ""
            elif prop["type"] == "status":
                details[key] = prop["status"]["name"]
            elif prop["type"] == "date":
                details[key] = prop["date"]["start"] if prop["date"] else "N/A"
            else:
                details[key] = "N/A"

        return details

    except Exception as e:
        logging.error(f"Task detail fetch error: {e}")
        return f"❌ Failed to fetch details: {str(e)}"
