"""Add amount_usd column for USD conversion

Revision ID: 003_add_amount_usd
Revises: 002_payshack_metadata
Create Date: 2026-01-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_amount_usd'
down_revision = '002_payshack_metadata'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add amount_usd column to transactions table."""
    # Add amount_usd column
    op.add_column(
        'transactions',
        sa.Column('amount_usd', sa.Numeric(18, 4), nullable=True)
    )
    
    # Add fee_usd column
    op.add_column(
        'transactions',
        sa.Column('fee_usd', sa.Numeric(18, 4), nullable=True)
    )
    
    # Add exchange_rate column for audit/reference
    op.add_column(
        'transactions',
        sa.Column('exchange_rate', sa.Numeric(12, 8), nullable=True)
    )
    
    # Create index for USD amount queries
    op.create_index(
        'ix_transactions_amount_usd',
        'transactions',
        ['amount_usd'],
    )


def downgrade() -> None:
    """Remove amount_usd column from transactions table."""
    op.drop_index('ix_transactions_amount_usd', table_name='transactions')
    op.drop_column('transactions', 'exchange_rate')
    op.drop_column('transactions', 'fee_usd')
    op.drop_column('transactions', 'amount_usd')
