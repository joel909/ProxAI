import json

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


def get_tool_config(provider):
    credential = get_tool_credential(provider)
    if credential is None or not credential.config_json:
        return {}

    try:
        return json.loads(credential.config_json)
    except (TypeError, json.JSONDecodeError):
        return {}


def get_tool_help(provider):
    """Return safe setup metadata for one configured tool provider."""
    if not isinstance(provider, str) or not provider.strip():
        return {
            "error": "A tool provider name is required.",
            "available_tools": list_tool_providers(),
        }

    requested_provider = provider.strip().casefold()
    with Session(engine) as session:
        credentials = list(session.scalars(select(ToolCredentialTable)))
        matches = [
            item
            for item in credentials
            if item.provider.casefold() == requested_provider
        ]
        credential = next(
            (item for item in matches if item.enabled and item.api_key),
            next(
                (item for item in matches if item.provider == provider.strip()),
                matches[0] if matches else None,
            ),
        )

        if credential is None:
            return {
                "error": f"No setup instructions were found for '{provider}'.",
                "available_tools": list_tool_providers(),
            }

        return {
            "tool": credential.provider,
            "required_token": credential.required_token,
            "configured": bool(credential.enabled and credential.api_key),
            "setup_instructions": credential.setup_instructions,
        }


def list_tool_providers():
    """List enabled provider names without exposing stored credentials."""
    with Session(engine) as session:
        providers = list(
            session.scalars(
                select(ToolCredentialTable.provider)
                .where(ToolCredentialTable.enabled.is_(True))
                .order_by(ToolCredentialTable.provider)
            )
        )

    unique_providers = {}
    for provider in providers:
        unique_providers.setdefault(provider.casefold(), provider)
    return list(unique_providers.values())


def save_tool_api_key(provider, api_key, config=None):
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

        if config is not None:
            credential.config_json = json.dumps(config)

        session.commit()
