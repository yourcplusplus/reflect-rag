"""async document ingestion queue fields

Adds the task-queue columns to ``documents``: ``attempts`` (retry counter),
``task_id`` (queue task id), ``content_hash`` (sha256 idempotency key, unique
index) and ``updated_at`` (crash-recovery staleness check).

The LangGraph ``checkpoint_*`` tables created by PostgresSaver.setup() are
deliberately ignored here (and by ``migrations/env.py``): they belong to
langgraph-checkpoint-postgres, not to this schema, and an autogenerate run must
never drop them.

Revision ID: f0f2c3783e6a
Revises: 8ca82791ae73
Create Date: 2026-10-24 05:24:27.392043+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f0f2c3783e6a'
down_revision: Union[str, Sequence[str], None] = '8ca82791ae73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'documents',
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
    )
    op.add_column('documents', sa.Column('task_id', sa.String(length=64), nullable=True))
    op.add_column('documents', sa.Column('content_hash', sa.String(length=64), nullable=True))
    op.add_column(
        'documents',
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
    )
    # 幂等兜底：唯一索引让并发重复上传在数据库层也只成功一次
    op.create_index('ix_documents_content_hash', 'documents', ['content_hash'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_documents_content_hash', table_name='documents')
    op.drop_column('documents', 'updated_at')
    op.drop_column('documents', 'content_hash')
    op.drop_column('documents', 'task_id')
    op.drop_column('documents', 'attempts')
