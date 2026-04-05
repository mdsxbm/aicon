"""把 assistant 事件编码成 SSE 文本块的辅助函数。"""

from __future__ import annotations

import json
from typing import Any

from src.assistant.serialization import to_jsonable


def encode_sse_event(event_type: str, payload: Any) -> str:
    """编码单条 SSE 事件。

    参数说明：
    - event_type: 事件类型，例如 assistant.message。
    - payload: 事件负载，会被序列化到 data 字段。
    """
    body = json.dumps(
        {"type": event_type, "data": to_jsonable(payload)},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return f"data: {body}\n\n"
