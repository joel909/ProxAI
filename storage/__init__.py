from datetime import datetime, timezone
import random
import string

from sqlalchemy import UniqueConstraint, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy import ForeignKey

class Base(DeclarativeBase):
    pass

class ProviderDB(Base):
    __tablename__ = "providers"
    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(nullable=False)
    default_model: Mapped[str] = mapped_column(nullable=False)
    api_token : Mapped[str] = mapped_column(nullable=False)
    warning_token_limit: Mapped[int] = mapped_column(default=100000)
    __table_args__ = (
        UniqueConstraint("api_token", "default_model"),
    )

# this will store all the chats every happend
class AllChatsTable(Base):
    __tablename__ = "chats"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.conversation_id"),index=True)
    role: Mapped[str] = mapped_column(nullable=False)
    message: Mapped[str] = mapped_column(nullable=False)
    timestamp: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

# this is the intermediatry table that will store the conversation id and the provider used for joins with tool table
class ConversationTable(Base):
    __tablename__ = "conversations"
    timestamp: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    conversation_id: Mapped[str] = mapped_column(primary_key=True,index=True)
    provider: Mapped[str] = mapped_column(nullable=False)

#This table will store the tool call history for each conversation
class ToolCallHistoryTable(Base):
    __tablename__ = "tool_call_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.conversation_id"),index=True)
    tool_name: Mapped[str] = mapped_column(nullable=False)
    tool_call_id: Mapped[str] = mapped_column(nullable=False,unique=True)
    output: Mapped[str] = mapped_column(nullable=False)
    output_type : Mapped[str] = mapped_column(nullable=False)
    timestamp: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

engine = create_engine("sqlite:///assistant.db")
Base.metadata.create_all(engine)

class ChatHistoryManager:
    def __init__(self):
        self.engine = engine
        self.conversation_id = self.generate_conversation_id()
    def generate_conversation_id(self):
        characters = string.ascii_letters + string.digits
        random_string = ''.join(random.choices(characters, k=30))
        return random_string       

    def store_chat_history(self, role, message):
       #keep the imports local to avoid circular imports
       from storage.store_chat_history import store_chat_history

       return store_chat_history(role, message, self.conversation_id)
    def store_tool_call_history(self, tool_name, tool_call_id, output, output_type):
        from storage.store_tool_response_history import store_tool_response_history
        return store_tool_response_history(tool_name, tool_call_id, output, output_type, self.conversation_id)

    def read_chat_history(self, include_tool_outputs=False):
        #keep the imports local to avoid circular imports
        from storage.read_chat_history import read_chat_history

        return read_chat_history(self.conversation_id, include_tool_outputs=include_tool_outputs)
