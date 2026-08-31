from sqlalchemy import select
from sqlalchemy.orm import Session

from . import AllChatsTable, engine


def list_conversations(limit=100):
    """Summarize chats directly from saved messages for legacy compatibility."""
    with Session(engine) as session:
        rows = session.execute(
            select(
                AllChatsTable.conversation_id,
                AllChatsTable.role,
                AllChatsTable.message,
                AllChatsTable.timestamp,
            ).order_by(AllChatsTable.timestamp.desc(), AllChatsTable.id.desc())
        ).all()

    conversations = {}
    for conversation_id, role, message, timestamp in rows:
        if conversation_id not in conversations:
            conversations[conversation_id] = {
                "id": conversation_id,
                "title": "New conversation",
                "preview": str(message).replace("\n", " ")[:120],
                "updated_at": timestamp.isoformat() if timestamp else None,
                "message_count": 0,
            }
        item = conversations[conversation_id]
        item["message_count"] += 1
        # Newest rows are visited first, so this ends on the earliest user prompt.
        if role == "user" and str(message).strip():
            item["title"] = str(message).strip().replace("\n", " ")[:64]

    safe_limit = max(1, min(int(limit), 500))
    return list(conversations.values())[:safe_limit]


def get_conversation_messages(conversation_id):
    with Session(engine) as session:
        rows = session.execute(
            select(AllChatsTable.role, AllChatsTable.message)
            .where(AllChatsTable.conversation_id == conversation_id)
            .order_by(AllChatsTable.timestamp, AllChatsTable.id)
        ).all()
    return [
        {"role": role, "content": message}
        for role, message in rows
        if role in {"user", "assistant"}
    ]
