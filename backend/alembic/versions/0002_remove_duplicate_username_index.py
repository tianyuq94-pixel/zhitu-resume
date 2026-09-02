"""Remove the duplicate username uniqueness index.

Revision ID: 0002_username_index
Revises: 0001_users_profiles
"""
from typing import Sequence

from alembic import op

revision: str = "0002_username_index"
down_revision: str | None = "0001_users_profiles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("uq_users_username", table_name="users")


def downgrade() -> None:
    op.create_index("uq_users_username", "users", ["username"], unique=True)

