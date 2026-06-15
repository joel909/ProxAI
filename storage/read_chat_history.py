from pathlib import Path
import json

ALLOWED_CHAT_ROLES = {"user", "assistant", "tool_response"}


def read_chat_history(temp_file_name):
    temp_file_path = Path(temp_file_name)
    if not temp_file_path.exists():
        return json.dumps({"messages": []}, indent=2)

    file_contents = temp_file_path.read_text().strip()
    if not file_contents:
        return json.dumps({"messages": []}, indent=2)

    try:
        chat_history = json.loads(file_contents)
    except json.JSONDecodeError:
        chat_history = {
            "messages": [
                {
                    "role": "legacy",
                    "content": file_contents,
                }
            ]
        }

    if isinstance(chat_history, list):
        messages = chat_history
    elif isinstance(chat_history, dict):
        messages = chat_history.get("messages", [])
    else:
        messages = []

    normalized_messages = []
    for message in messages:
        if not isinstance(message, dict):
            continue

        role = str(message.get("role", "user")).lower()
        if role not in ALLOWED_CHAT_ROLES:
            role = "user"

        content = message.get("content", "")
        if not isinstance(content, str):
            content = json.dumps(content)

        normalized_messages.append(
            {
                "role": role,
                "content": content,
            }
        )

    chat_history = {"messages": normalized_messages}
    return json.dumps(chat_history, indent=2)
