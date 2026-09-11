"""Add resumable, owner-scoped agent tasks."""
from alembic import op
import sqlalchemy as sa

revision = '0009_agent_runs'
down_revision = '0008_stored_files'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('agent_runs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(205), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.create_index('ix_agent_runs_user_id', 'agent_runs', ['user_id'])


def downgrade():
    op.drop_table('agent_runs')
