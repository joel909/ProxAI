from sqlalchemy import literal, select, union_all
from storage import AllChatsTable, Session, ToolCallHistoryTable
from . import engine
import json

ALLOWED_CHAT_ROLES = {"user", "assistant", "tool_response"}

def read_chat_history(conversation_id, include_tool_outputs=False):

    with Session(engine) as session:
        chats_query = select(
            AllChatsTable.conversation_id.label("conversation_id"),
            AllChatsTable.role.label("role"),
            AllChatsTable.message.label("message"),
            AllChatsTable.timestamp.label("timestamp"),
            literal(None).label("tool_call_id"),
            literal(None).label("output"),
            literal(None).label("output_type"),
            literal(None).label("tool_name"),
        ).where(AllChatsTable.conversation_id == conversation_id)

        tool_calls_query = select(
            ToolCallHistoryTable.conversation_id.label("conversation_id"),
            literal("tool_response").label("role"),
            ToolCallHistoryTable.output.label("message"),
            ToolCallHistoryTable.timestamp.label("timestamp"),
            ToolCallHistoryTable.tool_call_id.label("tool_call_id"),
            ToolCallHistoryTable.output.label("output"),
            ToolCallHistoryTable.output_type.label("output_type"),
            ToolCallHistoryTable.tool_name.label("tool_name"),
        ).where(
            ToolCallHistoryTable.conversation_id == conversation_id,
            ToolCallHistoryTable.tool_name != "read_memory" 
            )
        if include_tool_outputs:
            history_events = union_all(chats_query, tool_calls_query).subquery()
        else:
            history_events = chats_query.subquery()
        messages = session.execute(
            select(history_events).order_by(history_events.c.timestamp)
        ).mappings().all()

        chat_history = {
            "messages": [
                {"role": message["role"], "content": message["message"]}
                for message in messages
            ]
        }
        # print(f"Read chat history for conversation_id {conversation_id}: {chat_history}")

    return json.dumps(chat_history, indent=2)
