"""update agent statistics model

Revision ID: 1c1324e56ad1
Revises: add_is_agent_field
Create Date: 2025-01-31 11:55:20.505629

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1c1324e56ad1'
down_revision: Union[str, None] = 'add_is_agent_field'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_agents_id', table_name='agents')
    op.drop_table('agents')
    op.drop_index('ix_main_users_id', table_name='main_users')
    op.drop_table('main_users')
    op.alter_column('agent_prices', 'agent_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('agent_prices', 'dynamic_proxy_price',
               existing_type=sa.FLOAT(),
               type_=sa.Numeric(precision=10, scale=2),
               existing_nullable=True)
    op.alter_column('agent_prices', 'static_proxy_price',
               existing_type=sa.FLOAT(),
               type_=sa.Numeric(precision=10, scale=2),
               existing_nullable=True)
    op.alter_column('agent_prices', 'created_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('agent_prices', 'updated_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.create_index(op.f('ix_agent_prices_id'), 'agent_prices', ['id'], unique=False)
    op.alter_column('agent_statistics', 'total_users',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('agent_statistics', 'active_users',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('agent_statistics', 'total_orders',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('agent_statistics', 'active_orders',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('agent_statistics', 'total_consumption',
               existing_type=sa.FLOAT(),
               type_=sa.Numeric(precision=10, scale=2),
               nullable=False)
    op.alter_column('agent_statistics', 'monthly_consumption',
               existing_type=sa.FLOAT(),
               type_=sa.Numeric(precision=10, scale=2),
               nullable=False)
    op.alter_column('agent_statistics', 'dynamic_resource_count',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('agent_statistics', 'static_resource_count',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('instances', 'created_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('instances', 'updated_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('proxy_info', 'created_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('proxy_info', 'updated_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.drop_index('ix_proxy_info_id', table_name='proxy_info')
    op.add_column('resource_types', sa.Column('description', sa.String(length=255), nullable=True))
    op.add_column('resource_types', sa.Column('status', sa.String(length=20), nullable=True))
    op.alter_column('resource_types', 'created_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('resource_types', 'updated_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('resource_usage', 'created_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('resource_usage', 'updated_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.add_column('resource_usage_history', sa.Column('usage_amount', sa.Float(), nullable=True))
    op.add_column('resource_usage_history', sa.Column('usage_type', sa.String(length=50), nullable=True))
    op.add_column('resource_usage_history', sa.Column('remark', sa.String(length=255), nullable=True))
    op.alter_column('resource_usage_history', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('resource_usage_history', 'resource_type_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('resource_usage_history', 'created_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('resource_usage_history', 'updated_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.drop_index('ix_resource_usage_history_id', table_name='resource_usage_history')
    op.drop_constraint(None, 'resource_usage_history', type_='foreignkey')
    op.drop_column('resource_usage_history', 'agent_id')
    op.drop_column('resource_usage_history', 'status')
    op.alter_column('resource_usage_statistics', 'resource_type_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('resource_usage_statistics', 'created_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('resource_usage_statistics', 'updated_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.drop_index('ix_resource_usage_statistics_id', table_name='resource_usage_statistics')
    op.add_column('transactions', sa.Column('agent_id', sa.Integer(), nullable=True))
    op.alter_column('transactions', 'created_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('transactions', 'updated_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.create_foreign_key(None, 'transactions', 'users', ['agent_id'], ['id'])
    op.alter_column('users', 'password',
               existing_type=sa.VARCHAR(length=100),
               type_=sa.String(length=255),
               nullable=True)
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(length=100),
               type_=sa.String(length=255),
               existing_nullable=True)
    op.alter_column('users', 'remark',
               existing_type=sa.VARCHAR(length=500),
               type_=sa.String(length=255),
               existing_nullable=True)
    op.alter_column('users', 'created_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('users', 'updated_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.create_foreign_key(None, 'users', 'users', ['agent_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.create_foreign_key(None, 'users', 'agents', ['agent_id'], ['id'])
    op.alter_column('users', 'updated_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('users', 'created_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('users', 'remark',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=500),
               existing_nullable=True)
    op.alter_column('users', 'email',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=100),
               existing_nullable=True)
    op.alter_column('users', 'password',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=100),
               nullable=False)
    op.drop_constraint(None, 'transactions', type_='foreignkey')
    op.alter_column('transactions', 'updated_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('transactions', 'created_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.drop_column('transactions', 'agent_id')
    op.create_index('ix_resource_usage_statistics_id', 'resource_usage_statistics', ['id'], unique=False)
    op.alter_column('resource_usage_statistics', 'updated_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('resource_usage_statistics', 'created_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('resource_usage_statistics', 'resource_type_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.add_column('resource_usage_history', sa.Column('status', sa.VARCHAR(length=7), nullable=True))
    op.add_column('resource_usage_history', sa.Column('agent_id', sa.INTEGER(), nullable=False))
    op.create_foreign_key(None, 'resource_usage_history', 'agents', ['agent_id'], ['id'])
    op.create_index('ix_resource_usage_history_id', 'resource_usage_history', ['id'], unique=False)
    op.alter_column('resource_usage_history', 'updated_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('resource_usage_history', 'created_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('resource_usage_history', 'resource_type_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('resource_usage_history', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_column('resource_usage_history', 'remark')
    op.drop_column('resource_usage_history', 'usage_type')
    op.drop_column('resource_usage_history', 'usage_amount')
    op.alter_column('resource_usage', 'updated_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('resource_usage', 'created_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('resource_types', 'updated_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('resource_types', 'created_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.drop_column('resource_types', 'status')
    op.drop_column('resource_types', 'description')
    op.create_index('ix_proxy_info_id', 'proxy_info', ['id'], unique=False)
    op.alter_column('proxy_info', 'updated_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('proxy_info', 'created_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('instances', 'updated_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('instances', 'created_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('agent_statistics', 'static_resource_count',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('agent_statistics', 'dynamic_resource_count',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('agent_statistics', 'monthly_consumption',
               existing_type=sa.Numeric(precision=10, scale=2),
               type_=sa.FLOAT(),
               nullable=True)
    op.alter_column('agent_statistics', 'total_consumption',
               existing_type=sa.Numeric(precision=10, scale=2),
               type_=sa.FLOAT(),
               nullable=True)
    op.alter_column('agent_statistics', 'active_orders',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('agent_statistics', 'total_orders',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('agent_statistics', 'active_users',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('agent_statistics', 'total_users',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.drop_index(op.f('ix_agent_prices_id'), table_name='agent_prices')
    op.alter_column('agent_prices', 'updated_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('agent_prices', 'created_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
    op.alter_column('agent_prices', 'static_proxy_price',
               existing_type=sa.Numeric(precision=10, scale=2),
               type_=sa.FLOAT(),
               existing_nullable=True)
    op.alter_column('agent_prices', 'dynamic_proxy_price',
               existing_type=sa.Numeric(precision=10, scale=2),
               type_=sa.FLOAT(),
               existing_nullable=True)
    op.alter_column('agent_prices', 'agent_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.create_table('main_users',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('username', sa.VARCHAR(length=50), nullable=False),
    sa.Column('app_username', sa.VARCHAR(length=50), nullable=False),
    sa.Column('password', sa.VARCHAR(length=64), nullable=True),
    sa.Column('phone', sa.VARCHAR(length=20), nullable=True),
    sa.Column('email', sa.VARCHAR(length=64), nullable=True),
    sa.Column('auth_type', sa.INTEGER(), nullable=True),
    sa.Column('auth_name', sa.VARCHAR(length=64), nullable=True),
    sa.Column('auth_no', sa.VARCHAR(length=64), nullable=True),
    sa.Column('status', sa.INTEGER(), nullable=True),
    sa.Column('balance', sa.FLOAT(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('app_username'),
    sa.UniqueConstraint('username')
    )
    op.create_index('ix_main_users_id', 'main_users', ['id'], unique=False)
    op.create_table('agents',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('username', sa.VARCHAR(length=50), nullable=False),
    sa.Column('password', sa.VARCHAR(length=100), nullable=False),
    sa.Column('email', sa.VARCHAR(length=100), nullable=True),
    sa.Column('balance', sa.FLOAT(), nullable=True),
    sa.Column('status', sa.VARCHAR(length=20), nullable=True),
    sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_index('ix_agents_id', 'agents', ['id'], unique=False)
    # ### end Alembic commands ###
