"""Fix country field - increase length from 2 to 10

Revision ID: 004_fix_country_field
Revises: 003_add_amount_usd
Create Date: 2026-01-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_fix_country_field'
down_revision = '003_add_amount_usd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Increase country field length from 2 to 10 characters."""
    # Alter column to allow longer country codes
    op.alter_column(
        'transactions',
        'country',
        existing_type=sa.String(2),
        type_=sa.String(10),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Revert country field to 2 characters (may truncate data!)."""
    op.alter_column(
        'transactions',
        'country',
        existing_type=sa.String(10),
        type_=sa.String(2),
        existing_nullable=True,
    )
