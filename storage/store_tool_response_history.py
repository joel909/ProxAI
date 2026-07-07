from . import  ToolCallHistoryTable, engine
from sqlalchemy.orm import Session

def store_tool_response_history(tool_name, tool_call_id, output, output_type, conversation_id):
    with Session(engine) as session:
        tool_call = ToolCallHistoryTable(
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            output=str(output),
            output_type=output_type,
            conversation_id=conversation_id
        )
        session.add(tool_call)
        session.commit()