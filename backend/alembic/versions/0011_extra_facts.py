"""Private supplementary career facts."""
from alembic import op
import sqlalchemy as sa

revision = "0011_extra_facts"
down_revision = "0010_agent_budgets"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user_profiles", sa.Column("extra_facts", sa.JSON(), nullable=True))
    op.add_column("user_profiles", sa.Column("facts_revision", sa.Integer(), nullable=False, server_default="0"))


def downgrade():
    op.drop_column("user_profiles", "facts_revision")
    op.drop_column("user_profiles", "extra_facts")
