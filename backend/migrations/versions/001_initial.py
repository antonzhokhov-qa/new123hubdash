"""Initial migration - create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2026-01-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('source', sa.String(20), nullable=False),
        sa.Column('source_id', sa.String(255), nullable=False),
        sa.Column('reference_id', sa.String(255), nullable=True),
        sa.Column('client_operation_id', sa.String(255), nullable=True),
        sa.Column('order_id', sa.String(255), nullable=True),
        sa.Column('project', sa.String(100), nullable=True),
        sa.Column('merchant_id', sa.String(255), nullable=True),
        sa.Column('amount', sa.Numeric(18, 4), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='INR'),
        sa.Column('fee', sa.Numeric(18, 4), nullable=True),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('original_status', sa.String(50), nullable=True),
        sa.Column('user_id', sa.String(255), nullable=True),
        sa.Column('user_email', sa.String(255), nullable=True),
        sa.Column('user_phone', sa.String(50), nullable=True),
        sa.Column('user_name', sa.String(255), nullable=True),
        sa.Column('country', sa.String(2), nullable=True),
        sa.Column('utr', sa.String(100), nullable=True),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('payment_product', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source_create_cursor', sa.String(100), nullable=True),
        sa.Column('source_update_cursor', sa.String(100), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(), nullable=True),
        sa.Column('data_hash', sa.String(64), nullable=True),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for transactions
    op.create_index('idx_txn_source', 'transactions', ['source'])
    op.create_index('idx_txn_source_date', 'transactions', ['source', 'created_at'])
    op.create_index('idx_txn_project', 'transactions', ['project'])
    op.create_index('idx_txn_status', 'transactions', ['status'])
    op.create_index('idx_txn_client_op_id', 'transactions', ['client_operation_id'])
    op.create_index('idx_txn_order_id', 'transactions', ['order_id'])
    op.create_index('idx_txn_reference_id', 'transactions', ['reference_id'])
    op.create_index('idx_txn_data_hash', 'transactions', ['data_hash'], unique=True)
    op.create_index('idx_txn_created_at', 'transactions', [sa.text('created_at DESC')])

    # Create sync_state table
    op.create_table(
        'sync_state',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source', sa.String(20), nullable=False),
        sa.Column('last_create_cursor', sa.String(100), nullable=True),
        sa.Column('last_update_cursor', sa.String(100), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_successful_sync', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_status', sa.String(20), server_default='idle', nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('records_synced', sa.Integer(), server_default='0', nullable=True),
        sa.Column('total_records', sa.Integer(), server_default='0', nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source')
    )

    # Initialize sync_state
    op.execute("INSERT INTO sync_state (source) VALUES ('vima'), ('payshack')")

    # Create reconciliation_runs table
    op.create_table(
        'reconciliation_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('recon_date', sa.Date(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_vima', sa.Integer(), server_default='0', nullable=True),
        sa.Column('total_payshack', sa.Integer(), server_default='0', nullable=True),
        sa.Column('matched', sa.Integer(), server_default='0', nullable=True),
        sa.Column('discrepancies', sa.Integer(), server_default='0', nullable=True),
        sa.Column('missing_vima', sa.Integer(), server_default='0', nullable=True),
        sa.Column('missing_payshack', sa.Integer(), server_default='0', nullable=True),
        sa.Column('status', sa.String(20), server_default='running', nullable=True),
        sa.Column('error_message', sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_recon_runs_date', 'reconciliation_runs', ['recon_date'])

    # Create reconciliation_results table
    op.create_table(
        'reconciliation_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('recon_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recon_date', sa.Date(), nullable=False),
        sa.Column('vima_txn_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('payshack_txn_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('client_operation_id', sa.String(255), nullable=True),
        sa.Column('match_status', sa.String(30), nullable=False),
        sa.Column('discrepancy_type', sa.String(50), nullable=True),
        sa.Column('vima_amount', sa.Numeric(18, 4), nullable=True),
        sa.Column('payshack_amount', sa.Numeric(18, 4), nullable=True),
        sa.Column('amount_diff', sa.Numeric(18, 4), nullable=True),
        sa.Column('vima_status', sa.String(30), nullable=True),
        sa.Column('payshack_status', sa.String(30), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['recon_run_id'], ['reconciliation_runs.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_recon_results_date_status', 'reconciliation_results', ['recon_date', 'match_status'])
    op.create_index('idx_recon_results_run', 'reconciliation_results', ['recon_run_id'])
    op.create_index('idx_recon_results_client_op', 'reconciliation_results', ['client_operation_id'])


def downgrade() -> None:
    op.drop_table('reconciliation_results')
    op.drop_table('reconciliation_runs')
    op.drop_table('sync_state')
    op.drop_table('transactions')
