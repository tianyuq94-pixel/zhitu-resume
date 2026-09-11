"""Persistent agent limits across serverless instances."""
from alembic import op
import sqlalchemy as sa
revision = '0010_agent_budgets'
down_revision = '0009_agent_runs'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('agent_budgets', sa.Column('key', sa.String(90), primary_key=True),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.BigInteger(), nullable=False))
    op.create_index('ix_agent_budgets_expires_at', 'agent_budgets', ['expires_at'])


def downgrade():
    op.drop_table('agent_budgets')
