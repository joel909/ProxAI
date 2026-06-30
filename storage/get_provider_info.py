from . import ProviderDB, engine
from sqlalchemy.orm import Session
from sqlalchemy import select

def get_provider_info():
    with Session(engine) as session:
        provider_info = session.scalars(select(ProviderDB)).all()
        return provider_info
    