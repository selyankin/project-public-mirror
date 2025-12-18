"""Create tables for check results, cache, and reports."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = '20241006_add_check_entities'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Создаёт таблицы для результатов проверок и отчётов."""
    op.create_table(
        'check_results',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'schema_version',
            sa.Integer(),
            server_default='1',
            nullable=False,
        ),
        sa.Column('kind', sa.Text(), nullable=False),
        sa.Column('input_value', sa.Text(), nullable=False),
        sa.Column('payload', postgresql.JSONB(), nullable=False),
    )

    op.create_table(
        'check_cache',
        sa.Column('cache_key', sa.Text(), primary_key=True, nullable=False),
        sa.Column(
            'check_result_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            'cache_version',
            sa.Text(),
            server_default='v1',
            nullable=False,
        ),
    )
    op.create_index(
        'ix_check_cache_expires_at',
        'check_cache',
        ['expires_at'],
    )

    op.create_table(
        'reports',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'check_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column(
            'modules',
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column('payload', postgresql.JSONB(), nullable=False),
    )


def downgrade() -> None:
    """Откатывает создание таблиц отчётов и результатов проверок."""
    op.drop_table('reports')
    op.drop_index('ix_check_cache_expires_at', table_name='check_cache')
    op.drop_table('check_cache')
    op.drop_table('check_results')
