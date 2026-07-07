from . import  engine, AllChatsTable
from sqlalchemy.orm import Session

def store_chat_history(role,message,conversation_id):
    with Session(engine) as session:
        chat = AllChatsTable(
            role=role,
            message=message,
            conversation_id=conversation_id
        )
        session.add(chat)
        session.commit()
