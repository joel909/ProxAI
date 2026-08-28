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
    config_json: Mapped[Optional[str]] = mapped_column(nullable=True)
    setup_instructions: Mapped[Optional[str]] = mapped_column(nullable=True)
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
    if "config_json" not in column_names:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE tool_credentials ADD COLUMN config_json VARCHAR")
            )
    if "setup_instructions" not in column_names:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE tool_credentials "
                    "ADD COLUMN setup_instructions VARCHAR"
                )
            )


migrate_tool_credentials_schema()

DEFAULT_TOOL_CREDENTIALS = [
    {
        "provider": "firecrawl",
        "api_key": None,
        "required_token": "API Key",
        "setup_instructions": (
            "Open the Firecrawl dashboard, create an API key, then run /setup-tools "
            "and choose Firecrawl. Paste only the API key. ProxAI validates it with "
            "a small search before saving it. If validation fails, check that the key "
            "was copied completely, is active, has available usage, and that the "
            "machine can connect to Firecrawl."
        ),
        "enabled": True,
    },
    {
        "provider":"github",
        "api_key": None,
        "required_token": "PAT token",
        "setup_instructions": (
            "Open GitHub Settings > Developer settings > Personal access tokens > "
            "Tokens (classic), then generate a personal access token (classic). Give "
            "it a descriptive name, choose an expiration, and enable the repo scope "
            "if ProxAI must access private repositories. Run /setup-tools, choose "
            "GitHub, and paste only the token. If validation fails, verify that the "
            "token is not expired or revoked and that it has the required repository "
            "access. Create one at https://github.com/settings/personal-access-tokens/new."
        ),
        "enabled": True,
    },
    {
        "provider":"Cloudflare",
        "api_key": None,
        "required_token": "API token",
        "setup_instructions": (
            "Open Cloudflare Profile > API Tokens and create a custom API token. Add "
            "Account > Cloudflare Tunnel > Edit and Zone > DNS > Edit, and assign the "
            "intended account and zone resources. Run /setup-tools, choose Cloudflare, "
            "and paste only the raw token without 'Bearer' or 'Authorization:'. ProxAI "
            "checks authentication plus Tunnel and DNS permissions. If no zone is "
            "available, enter the 32-character Account ID and deployment will use the "
            "default domain. Permission errors mean the token's account/zone resources "
            "or Tunnel/DNS Edit permissions need to be corrected. Connection or HTTP "
            "errors should be retried after checking network access and token status."
        ),
        "enabled": True,
    }
]


def prefill_tool_credentials():
    # Creates default external tool credential rows once, so users can fill keys later.
    with Session(engine) as session:
        existing_providers = {
            provider.casefold()
            for provider in session.scalars(select(ToolCredentialTable.provider))
        }
        missing_credentials = [
            credential for credential in DEFAULT_TOOL_CREDENTIALS
            if credential["provider"].casefold() not in existing_providers
        ]
        session.add_all(
            ToolCredentialTable(
                provider=credential["provider"],
                api_key=credential["api_key"],
                required_token=credential["required_token"],
                setup_instructions=credential["setup_instructions"],
                enabled=credential["enabled"],
            )
            for credential in missing_credentials
        )

        required_tokens = {
            credential["provider"].casefold(): credential["required_token"]
            for credential in DEFAULT_TOOL_CREDENTIALS
        }
        setup_instructions = {
            credential["provider"].casefold(): credential["setup_instructions"]
            for credential in DEFAULT_TOOL_CREDENTIALS
        }
        for credential in session.scalars(select(ToolCredentialTable)):
            provider_key = credential.provider.casefold()
            if provider_key in required_tokens:
                credential.required_token = required_tokens[provider_key]
                credential.setup_instructions = setup_instructions[provider_key]

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
