"""trajectory record: annotations and analyses (Phase 1)

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0003'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('annotations',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('ts', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('target_kind', sa.String(), nullable=False),
    sa.Column('target_id', sa.String(), nullable=False),
    sa.Column('run_id', sa.String(), nullable=True),
    sa.Column('label', sa.String(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('author', sa.String(), nullable=False),
    sa.Column('detail', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_annotations_label'), 'annotations', ['label'], unique=False)
    op.create_index(op.f('ix_annotations_run_id'), 'annotations', ['run_id'], unique=False)
    op.create_index(op.f('ix_annotations_target_id'), 'annotations', ['target_id'], unique=False)
    op.create_table('analyses',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('ts', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('run_id', sa.String(), nullable=True),
    sa.Column('task_id', sa.String(), nullable=True),
    sa.Column('kind', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('label', sa.String(), nullable=False),
    sa.Column('method', sa.Text(), nullable=False),
    sa.Column('inputs', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('results', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('sources', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('author', sa.String(), nullable=False),
    sa.Column('operator_influenced', sa.Boolean(), nullable=False),
    sa.Column('location', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analyses_run_id'), 'analyses', ['run_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_analyses_run_id'), table_name='analyses')
    op.drop_table('analyses')
    op.drop_index(op.f('ix_annotations_target_id'), table_name='annotations')
    op.drop_index(op.f('ix_annotations_run_id'), table_name='annotations')
    op.drop_index(op.f('ix_annotations_label'), table_name='annotations')
    op.drop_table('annotations')
