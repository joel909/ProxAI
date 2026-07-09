from sqlalchemy import select
from sqlalchemy.orm import Session

from . import ToolCredentialTable, engine


def get_tool_credential(provider):
    with Session(engine) as session:
        return session.scalar(
            select(ToolCredentialTable).where(ToolCredentialTable.provider == provider)
        )


def get_tool_api_key(provider):
    credential = get_tool_credential(provider)
    if credential is None or not credential.enabled:
        return None

    return credential.api_key


def save_tool_api_key(provider, api_key):
    with Session(engine) as session:
        credential = session.scalar(
            select(ToolCredentialTable).where(ToolCredentialTable.provider == provider)
        )
        if credential is None:
            credential = ToolCredentialTable(
                provider=provider,
                api_key=api_key,
                enabled=True,
            )
            session.add(credential)
        else:
            credential.api_key = api_key
            credential.enabled = True

        session.commit()
