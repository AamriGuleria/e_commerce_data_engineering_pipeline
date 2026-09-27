"""add primary key to orders order_id

Revision ID: f4b12d9e63ac
Revises: c0ba64fcecb2
Create Date: 2026-09-27

"""
from typing import Sequence, Union

from alembic import op


revision: str = "f4b12d9e63ac"
down_revision: Union[str, Sequence[str], None] = "c0ba64fcecb2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_primary_key("pk_orders", "orders", ["order_id"])


def downgrade() -> None:
    op.drop_constraint("pk_orders", "orders", type_="primary")