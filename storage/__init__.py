from sqlalchemy import UniqueConstraint, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
class Base(DeclarativeBase):
    pass

class ProviderDB(Base):
    __tablename__ = "providers"
    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(nullable=False)
    default_model: Mapped[str] = mapped_column(nullable=False)
    api_token : Mapped[str] = mapped_column(nullable=False)
    __table_args__ = (
        UniqueConstraint("api_token", "default_model"),
    )

engine = create_engine("sqlite:///assistant.db")
Base.metadata.create_all(engine)