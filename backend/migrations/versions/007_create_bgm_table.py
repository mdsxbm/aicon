"""create bgm_files table

Revision ID: 007_create_bgm_table
Revises: 006_create_video_tasks_table
Create Date: 2024-12-04 12:18:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create bgm_files table
    op.create_table(
        'bgm_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, comment='主键ID'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='用户ID'),
        sa.Column('name', sa.String(200), nullable=False, comment='BGM名称'),
        sa.Column('file_name', sa.String(255), nullable=False, comment='原始文件名'),
        sa.Column('file_size', sa.Integer(), nullable=False, comment='文件大小（字节）'),
        sa.Column('file_key', sa.String(500), nullable=False, comment='MinIO对象键（存储路径）'),
        sa.Column('file_url', sa.String(500), nullable=True, comment='文件预签名URL（按需生成）'),
        sa.Column('duration', sa.Integer(), nullable=True, comment='音频时长（秒）'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active', comment='BGM状态'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    
    # Create indexes
    op.create_index('idx_bgm_user', 'bgm_files', ['user_id'])
    op.create_index('idx_bgm_status', 'bgm_files', ['status'])
    op.create_index('idx_bgm_created', 'bgm_files', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_bgm_created', table_name='bgm_files')
    op.drop_index('idx_bgm_status', table_name='bgm_files')
    op.drop_index('idx_bgm_user', table_name='bgm_files')
    
    # Drop table
    op.drop_table('bgm_files')
