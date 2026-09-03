from sqlalchemy import BigInteger, String
from sqlalchemy.dialects.mysql import LONGBLOB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class StoredFile(TimestampMixin, Base):
    """Private uploaded file persisted in the relational database."""

    __tablename__ = "stored_files"

    storage_key: Mapped[str] = mapped_column(String(255), primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    content: Mapped[bytes] = mapped_column(LONGBLOB, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
