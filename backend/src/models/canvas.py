import uuid
from enum import Enum

from sqlalchemy import CHAR, Column, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class CanvasGUID(TypeDecorator):
    """UUID type that round-trips cleanly on both PostgreSQL and SQLite."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgreSQLUUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(str(value))
        if dialect.name == "postgresql":
            return value
        return value.hex

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class CanvasItemType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"


class CanvasRunStatus(str, Enum):
    IDLE = "idle"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CanvasGenerationType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"


class CanvasDocument(BaseModel):
    __tablename__ = "canvas_documents"

    id = Column(CanvasGUID(), primary_key=True, default=uuid.uuid4, nullable=False, comment="主键ID")
    user_id = Column(CanvasGUID(), nullable=False, index=True, comment="用户ID")
    title = Column(String(200), nullable=False, comment="画布标题")
    description = Column(Text, nullable=True, comment="画布描述")

    items = relationship("CanvasItem", back_populates="document", cascade="all, delete-orphan")
    connections = relationship("CanvasConnection", back_populates="document", cascade="all, delete-orphan")
    generations = relationship("CanvasItemGeneration", back_populates="document", cascade="all, delete-orphan")


class CanvasItem(BaseModel):
    __tablename__ = "canvas_items"

    id = Column(CanvasGUID(), primary_key=True, default=uuid.uuid4, nullable=False, comment="主键ID")
    document_id = Column(
        CanvasGUID(),
        ForeignKey("canvas_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_type = Column(String(20), nullable=False, index=True, comment="节点类型")
    title = Column(String(200), nullable=False, default="", comment="节点标题")
    position_x = Column(Float, nullable=False, default=0)
    position_y = Column(Float, nullable=False, default=0)
    width = Column(Float, nullable=False, default=320)
    height = Column(Float, nullable=False, default=220)
    content_json = Column(JSON, nullable=False, default=dict)
    generation_config_json = Column(JSON, nullable=False, default=dict)
    last_run_status = Column(String(20), nullable=False, default=CanvasRunStatus.IDLE.value)
    last_run_error = Column(Text, nullable=True)
    last_output_json = Column(JSON, nullable=False, default=dict)
    z_index = Column(Integer, nullable=False, default=0)

    document = relationship("CanvasDocument", back_populates="items")
    generations = relationship("CanvasItemGeneration", back_populates="item", cascade="all, delete-orphan")


class CanvasConnection(BaseModel):
    __tablename__ = "canvas_connections"

    id = Column(CanvasGUID(), primary_key=True, default=uuid.uuid4, nullable=False, comment="主键ID")
    document_id = Column(
        CanvasGUID(),
        ForeignKey("canvas_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_item_id = Column(
        CanvasGUID(),
        ForeignKey("canvas_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_item_id = Column(
        CanvasGUID(),
        ForeignKey("canvas_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_handle = Column(String(20), nullable=False)
    target_handle = Column(String(20), nullable=False)

    document = relationship("CanvasDocument", back_populates="connections")


class CanvasItemGeneration(BaseModel):
    __tablename__ = "canvas_item_generations"

    id = Column(CanvasGUID(), primary_key=True, default=uuid.uuid4, nullable=False, comment="主键ID")
    item_id = Column(
        CanvasGUID(),
        ForeignKey("canvas_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id = Column(
        CanvasGUID(),
        ForeignKey("canvas_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(CanvasGUID(), nullable=False, index=True)
    generation_type = Column(String(20), nullable=False, index=True)
    request_payload_json = Column(JSON, nullable=False, default=dict)
    status = Column(String(20), nullable=False, default=CanvasRunStatus.IDLE.value)
    result_payload_json = Column(JSON, nullable=False, default=dict)
    error_message = Column(Text, nullable=True)

    item = relationship("CanvasItem", back_populates="generations")
    document = relationship("CanvasDocument", back_populates="generations")


def ensure_canvas_uuid(value):
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


__all__ = [
    "CanvasConnection",
    "CanvasDocument",
    "CanvasGenerationType",
    "CanvasItem",
    "CanvasItemGeneration",
    "CanvasItemType",
    "CanvasRunStatus",
    "ensure_canvas_uuid",
]
