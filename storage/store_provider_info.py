from . import ProviderDB, engine
from sqlalchemy.orm import Session

def save_provider_key(
    provider: str,
    api_token: str,
    default_model: str = "gpt-5.5",
    warning_token_limit: int = 100000,
):
    with Session(engine) as session:
        row = ProviderDB(
            provider=provider,
            api_token=api_token,
            default_model=default_model,
            warning_token_limit=warning_token_limit,
        )
        session.add(row)
        session.commit()
