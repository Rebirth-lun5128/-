"""initial — all tables

Revision ID: a5782f39d787
Revises:
Create Date: 2026-05-25 21:33:13.785243
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a5782f39d787'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'regions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('manager_id', sa.Integer(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('status', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['parent_id'], ['regions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'system_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('config_key', sa.String(50), nullable=False),
        sa.Column('config_value', sa.String(500), nullable=False),
        sa.Column('description', sa.String(200), nullable=True, server_default=''),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('config_key')
    )

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('openid', sa.String(100), nullable=True, server_default=''),
        sa.Column('unionid', sa.String(100), nullable=True, server_default=''),
        sa.Column('nickname', sa.String(100), nullable=True, server_default=''),
        sa.Column('avatar', sa.String(500), nullable=True, server_default=''),
        sa.Column('phone', sa.String(20), nullable=True, server_default=''),
        sa.Column('hashed_password', sa.String(200), nullable=True, server_default=''),
        sa.Column('role', sa.Enum('user', 'merchant', 'rider', 'region_admin', 'super_admin'), nullable=False, server_default='user'),
        sa.Column('region_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['region_id'], ['regions.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('openid')
    )

    op.create_table(
        'settlements',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('target_type', sa.Enum('restaurant', 'rider'), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('fee', sa.DECIMAL(10, 2), nullable=True, server_default='0'),
        sa.Column('net_amount', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('period', sa.String(20), nullable=True, server_default=''),
        sa.Column('status', sa.Enum('pending', 'paid'), nullable=True, server_default='pending'),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'restaurants',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('logo', sa.String(500), nullable=True, server_default=''),
        sa.Column('banner', sa.String(500), nullable=True, server_default=''),
        sa.Column('phone', sa.String(20), nullable=True, server_default=''),
        sa.Column('address', sa.String(300), nullable=True, server_default=''),
        sa.Column('lat', sa.DECIMAL(10, 7), nullable=True),
        sa.Column('lng', sa.DECIMAL(10, 7), nullable=True),
        sa.Column('category', sa.String(50), nullable=True, server_default=''),
        sa.Column('rating', sa.DECIMAL(2, 1), nullable=True, server_default='5.0'),
        sa.Column('monthly_sales', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('min_price', sa.DECIMAL(10, 2), nullable=True, server_default='0'),
        sa.Column('delivery_fee', sa.DECIMAL(10, 2), nullable=True, server_default='0'),
        sa.Column('delivery_time', sa.String(20), nullable=True, server_default='30分钟'),
        sa.Column('business_hours', sa.JSON(), nullable=True),
        sa.Column('notice', sa.String(200), nullable=True, server_default=''),
        sa.Column('status', sa.Enum('open', 'closed', 'resting'), nullable=True, server_default='closed'),
        sa.Column('verify_status', sa.Enum('unverified', 'verified', 'rejected'), nullable=True, server_default='unverified'),
        sa.Column('verify_method', sa.String(50), nullable=True, server_default=''),
        sa.Column('verify_note', sa.String(300), nullable=True, server_default=''),
        sa.Column('stall_location', sa.String(300), nullable=True, server_default=''),
        sa.Column('id_card_photo', sa.String(500), nullable=True, server_default=''),
        sa.Column('stall_photo', sa.String(500), nullable=True, server_default=''),
        sa.Column('region_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['region_id'], ['regions.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'user_addresses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('contact_name', sa.String(50), nullable=False),
        sa.Column('contact_phone', sa.String(20), nullable=False),
        sa.Column('gender', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('province', sa.String(50), nullable=True, server_default=''),
        sa.Column('city', sa.String(50), nullable=True, server_default=''),
        sa.Column('district', sa.String(50), nullable=True, server_default=''),
        sa.Column('detail', sa.String(200), nullable=False),
        sa.Column('lat', sa.DECIMAL(10, 7), nullable=True),
        sa.Column('lng', sa.DECIMAL(10, 7), nullable=True),
        sa.Column('label', sa.String(50), nullable=True, server_default=''),
        sa.Column('is_default', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'riders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('real_name', sa.String(50), nullable=False),
        sa.Column('id_card', sa.String(20), nullable=True, server_default=''),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('status', sa.Enum('offline', 'online', 'busy'), nullable=True, server_default='offline'),
        sa.Column('lat', sa.DECIMAL(10, 7), nullable=True),
        sa.Column('lng', sa.DECIMAL(10, 7), nullable=True),
        sa.Column('balance', sa.DECIMAL(10, 2), nullable=True, server_default='0'),
        sa.Column('total_orders', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('rating', sa.DECIMAL(2, 1), nullable=True, server_default='5.0'),
        sa.Column('audit_status', sa.Enum('pending', 'approved', 'rejected'), nullable=True, server_default='pending'),
        sa.Column('region_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['region_id'], ['regions.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'menu_categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('restaurant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'menu_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('restaurant_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('image', sa.String(500), nullable=True, server_default=''),
        sa.Column('price', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('original_price', sa.DECIMAL(10, 2), nullable=True),
        sa.Column('description', sa.String(300), nullable=True, server_default=''),
        sa.Column('monthly_sales', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('is_recommended', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('status', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['category_id'], ['menu_categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_no', sa.String(30), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('restaurant_id', sa.Integer(), nullable=False),
        sa.Column('rider_id', sa.Integer(), nullable=True),
        sa.Column('address_snapshot', sa.JSON(), nullable=False),
        sa.Column('items_total', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('delivery_fee', sa.DECIMAL(10, 2), nullable=True, server_default='0'),
        sa.Column('package_fee', sa.DECIMAL(10, 2), nullable=True, server_default='0'),
        sa.Column('discount_amount', sa.DECIMAL(10, 2), nullable=True, server_default='0'),
        sa.Column('total_price', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('status', sa.Enum('pending_pay', 'pending_accept', 'preparing', 'ready',
                                    'delivering', 'delivered', 'completed', 'cancelled'),
                  nullable=False, server_default='pending_pay'),
        sa.Column('cancel_reason', sa.String(300), nullable=True, server_default=''),
        sa.Column('cancel_by', sa.String(20), nullable=True, server_default=''),
        sa.Column('remark', sa.String(200), nullable=True, server_default=''),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('ready_at', sa.DateTime(), nullable=True),
        sa.Column('picked_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('region_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['region_id'], ['regions.id']),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id']),
        sa.ForeignKeyConstraint(['rider_id'], ['riders.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_no')
    )

    op.create_table(
        'order_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('menu_item_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('image', sa.String(500), nullable=True, server_default=''),
        sa.Column('price', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'order_timeline',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('description', sa.String(200), nullable=True, server_default=''),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'payment_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.String(64), nullable=True, server_default=''),
        sa.Column('out_trade_no', sa.String(64), nullable=True, server_default=''),
        sa.Column('amount', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('pay_type', sa.String(20), nullable=True, server_default='wechat_jsapi'),
        sa.Column('raw_notify', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('payment_records')
    op.drop_table('order_timeline')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('menu_items')
    op.drop_table('menu_categories')
    op.drop_table('riders')
    op.drop_table('user_addresses')
    op.drop_table('restaurants')
    op.drop_table('settlements')
    op.drop_table('users')
    op.drop_table('system_configs')
    op.drop_table('regions')
