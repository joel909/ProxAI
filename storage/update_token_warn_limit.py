from . import ProviderDB, engine
from sqlalchemy.orm import Session


def update_token_warning_limit(provider_id, new_limit):
    with Session(engine) as session:
        provider = session.get(ProviderDB, provider_id)
        if provider is None:
            raise ValueError(f"Provider with id {provider_id} was not found.")

        provider.warning_token_limit = new_limit
        session.commit()
