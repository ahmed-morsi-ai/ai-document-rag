"""add conversation titles

Revision ID: eab8407d6d14
Revises: d4f7a1b9c2e6
Create Date: 2026-08-23 19:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "eab8407d6d14"
down_revision: Union[str, Sequence[str], None] = "d4f7a1b9c2e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column("title", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("conversations", "title")
