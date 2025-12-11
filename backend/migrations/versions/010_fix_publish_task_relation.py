"""fix publish task relation to video_task

Revision ID: 010
Revises: 009
Create Date: 2025-12-11 13:30:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. 删除旧的chapter_id外键约束和索引
    op.drop_constraint('publish_tasks_chapter_id_fkey', 'publish_tasks', type_='foreignkey')
    op.drop_index('idx_publish_task_chapter', table_name='publish_tasks')
    
    # 2. 删除chapter_id列
    op.drop_column('publish_tasks', 'chapter_id')
    
    # 3. 添加video_task_id列
    op.add_column('publish_tasks', 
        sa.Column('video_task_id', postgresql.UUID(as_uuid=True), nullable=False, comment='视频任务外键')
    )
    
    # 4. 创建外键约束
    op.create_foreign_key(
        'publish_tasks_video_task_id_fkey',
        'publish_tasks', 'video_tasks',
        ['video_task_id'], ['id']
    )
    
    # 5. 创建索引
    op.create_index('idx_publish_task_video_task', 'publish_tasks', ['video_task_id'], unique=False)


def downgrade() -> None:
    # 回滚操作
    op.drop_index('idx_publish_task_video_task', table_name='publish_tasks')
    op.drop_constraint('publish_tasks_video_task_id_fkey', 'publish_tasks', type_='foreignkey')
    op.drop_column('publish_tasks', 'video_task_id')
    
    # 恢复chapter_id
    op.add_column('publish_tasks',
        sa.Column('chapter_id', postgresql.UUID(as_uuid=True), nullable=False, comment='章节外键')
    )
    op.create_foreign_key(
        'publish_tasks_chapter_id_fkey',
        'publish_tasks', 'chapters',
        ['chapter_id'], ['id']
    )
    op.create_index('idx_publish_task_chapter', 'publish_tasks', ['chapter_id'], unique=False)
