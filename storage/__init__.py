from datetime import datetime, timezone
import random
import string
from typing import Optional

from sqlalchemy import ForeignKey, UniqueConstraint, create_engine, inspect, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

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

# Stores user-provided config for external tool providers.
# Tool schemas and execution routing stay in code.
class ToolCredentialTable(Base):
    __tablename__ = "tool_credentials"
    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(nullable=False, unique=True)
    api_key: Mapped[Optional[str]] = mapped_column(nullable=True)
    required_token: Mapped[Optional[str]] = mapped_column(nullable=True)
    enabled: Mapped[bool] = mapped_column(default=True)

engine = create_engine("sqlite:///assistant.db")
Base.metadata.create_all(engine)


def migrate_tool_credentials_schema():
    """Add credential metadata columns for databases created by older releases."""
    column_names = {
        column["name"]
        for column in inspect(engine).get_columns(ToolCredentialTable.__tablename__)
    }
    if "required_token" not in column_names:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE tool_credentials ADD COLUMN required_token VARCHAR")
            )


migrate_tool_credentials_schema()

DEFAULT_TOOL_CREDENTIALS = [
    {
        "provider": "firecrawl",
        "api_key": None,
        "required_token": "API Key",
        "enabled": True,
    },
    {
        "provider":"github",
        "api_key": None,
        "required_token": "PAT token",
        "enabled": True,
    }
]


def prefill_tool_credentials():
    # Creates default external tool credential rows once, so users can fill keys later.
    with Session(engine) as session:
        existing_providers = set(session.scalars(select(ToolCredentialTable.provider)))
        missing_credentials = [
            credential for credential in DEFAULT_TOOL_CREDENTIALS
            if credential["provider"] not in existing_providers
        ]
        session.add_all(
            ToolCredentialTable(
                provider=credential["provider"],
                api_key=credential["api_key"],
                required_token=credential["required_token"],
                enabled=credential["enabled"],
            )
            for credential in missing_credentials
        )

        required_tokens = {
            credential["provider"]: credential["required_token"]
            for credential in DEFAULT_TOOL_CREDENTIALS
        }
        for credential in session.scalars(select(ToolCredentialTable)):
            if credential.provider in required_tokens:
                credential.required_token = required_tokens[credential.provider]

        session.commit()


prefill_tool_credentials()

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
