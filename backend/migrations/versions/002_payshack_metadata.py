"""PayShack metadata tables.

Revision ID: 002_payshack_metadata
Revises: 001_initial
Create Date: 2026-01-15 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_payshack_metadata'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PayShack Clients
    op.create_table(
        'payshack_clients',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', sa.String(100), nullable=False),
        sa.Column('reseller_id', sa.String(100), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('balance', sa.Numeric(20, 4), default=0),
        sa.Column('wallet_balance', sa.Numeric(20, 4), default=0),
        sa.Column('currency', sa.String(10), default='INR'),
        sa.Column('commission_rate', sa.Numeric(10, 4), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id'),
    )
    op.create_index('ix_payshack_clients_client_id', 'payshack_clients', ['client_id'], unique=True)
    op.create_index('ix_payshack_clients_reseller', 'payshack_clients', ['reseller_id'], unique=False)
    op.create_index('ix_payshack_clients_status', 'payshack_clients', ['status'], unique=False)

    # PayShack Resellers
    op.create_table(
        'payshack_resellers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reseller_id', sa.String(100), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('role', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('balance', sa.Numeric(20, 4), default=0),
        sa.Column('currency', sa.String(10), default='INR'),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reseller_id'),
    )
    op.create_index('ix_payshack_resellers_reseller_id', 'payshack_resellers', ['reseller_id'], unique=True)

    # PayShack Service Providers
    op.create_table(
        'payshack_service_providers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_id', sa.String(100), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('supports_payin', sa.Boolean(), default=True),
        sa.Column('supports_payout', sa.Boolean(), default=True),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider_id'),
    )
    op.create_index('ix_payshack_service_providers_provider_id', 'payshack_service_providers', ['provider_id'], unique=True)

    # PayShack Balance Snapshots
    op.create_table(
        'payshack_balance_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(100), nullable=False),
        sa.Column('entity_name', sa.String(255), nullable=True),
        sa.Column('balance', sa.Numeric(20, 4), nullable=False),
        sa.Column('currency', sa.String(10), default='INR'),
        sa.Column('snapshot_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_balance_snapshots_entity', 'payshack_balance_snapshots', ['entity_type', 'entity_id'], unique=False)
    op.create_index('ix_balance_snapshots_time', 'payshack_balance_snapshots', ['snapshot_at'], unique=False)
    op.create_index('ix_payshack_balance_snapshots_entity_id', 'payshack_balance_snapshots', ['entity_id'], unique=False)


def downgrade() -> None:
    op.drop_table('payshack_balance_snapshots')
    op.drop_table('payshack_service_providers')
    op.drop_table('payshack_resellers')
    op.drop_table('payshack_clients')
