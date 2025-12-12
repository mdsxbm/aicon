"""add account_id to publish_tasks

Revision ID: 012_add_account_id
Revises: 011_add_account_fields
Create Date: 2025-12-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 添加 account_id 列
    op.add_column('publish_tasks', sa.Column('account_id', UUID(as_uuid=True), nullable=True))
    
    # 添加外键约束
    op.create_foreign_key(
        'fk_publish_tasks_account_id',
        'publish_tasks',
        'bilibili_accounts',
        ['account_id'],
        ['id']
    )

def downgrade() -> None:
    op.drop_constraint('fk_publish_tasks_account_id', 'publish_tasks', type_='foreignkey')
    op.drop_column('publish_tasks', 'account_id')
