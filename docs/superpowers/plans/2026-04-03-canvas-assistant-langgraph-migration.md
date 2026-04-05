# Canvas Assistant LangGraph Migration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the canvas assistant experience from `ai-movie-studio` into `aicon` as a native Python/FastAPI + LangGraph assistant that reuses `aicon` canvas services and generation infrastructure.

**Architecture:** Build a new `aicon` assistant backend module that uses LangGraph only for high-level orchestration and keeps canvas reads, node CRUD, connection writes, and generation submission in explicit service-backed tools. On the frontend, embed a right-rail assistant in the existing canvas editor, reuse the timeline-oriented UI model from the old assistant, and bind it to a new `aicon` SSE protocol with confirmation/resume support.

**Tech Stack:** FastAPI, LangGraph, Pydantic, SQLAlchemy async session, existing `CanvasService`/`CanvasGenerationService`, Vue 3, Element Plus, SSE.

---

## File Structure

### Backend

- Create: `backend/src/api/schemas/canvas_assistant.py`
- Create: `backend/src/api/v1/canvas_assistant.py`
- Modify: `backend/src/api/v1/__init__.py`
- Create: `backend/src/assistant/__init__.py`
- Create: `backend/src/assistant/types.py`
- Create: `backend/src/assistant/session_store.py`
- Create: `backend/src/assistant/sse.py`
- Create: `backend/src/assistant/service.py`
- Create: `backend/src/assistant/prompts.py`
- Create: `backend/src/assistant/plans.py`
- Create: `backend/src/assistant/tools/__init__.py`
- Create: `backend/src/assistant/tools/canvas_tools.py`
- Create: `backend/src/assistant/tools/generation_tools.py`
- Create: `backend/src/assistant/graph/__init__.py`
- Create: `backend/src/assistant/graph/state.py`
- Create: `backend/src/assistant/graph/nodes.py`
- Create: `backend/src/assistant/graph/router.py`
- Create: `backend/src/assistant/graph/builder.py`
- Modify: `backend/pyproject.toml`
- Test: `backend/tests/unit/test_canvas_assistant_plans.py`
- Test: `backend/tests/unit/test_canvas_assistant_session_store.py`
- Test: `backend/tests/unit/test_canvas_assistant_tools.py`
- Test: `backend/tests/unit/test_canvas_assistant_service.py`
- Test: `backend/tests/integration/test_canvas_assistant_api.py`

### Frontend

- Create: `frontend/src/services/canvasAssistant.js`
- Create: `frontend/src/composables/useCanvasAssistant.js`
- Create: `frontend/src/composables/useCanvasAssistantTimeline.js`
- Create: `frontend/src/components/canvas/CanvasAssistant.vue`
- Create: `frontend/src/components/canvas/assistant/CanvasAssistantHeader.vue`
- Create: `frontend/src/components/canvas/assistant/CanvasAssistantTimeline.vue`
- Create: `frontend/src/components/canvas/assistant/CanvasAssistantMessageItem.vue`
- Create: `frontend/src/components/canvas/assistant/CanvasAssistantComposer.vue`
- Create: `frontend/src/components/canvas/assistant/CanvasAssistantConfirmationCard.vue`
- Create: `frontend/src/components/canvas/assistant/CanvasAssistantToolSummary.vue`
- Modify: `frontend/src/views/canvas/CanvasEditor.vue`
- Test: `frontend/src/tests/unit/composables/useCanvasAssistantTimeline.test.js`
- Test: `frontend/src/tests/unit/services/canvasAssistant.test.js`

### Reference Files To Read During Implementation

- Read: `frontend/src/views/canvas/CanvasEditor.vue`
- Read: `frontend/src/services/canvas.js`
- Read: `backend/src/api/v1/canvas.py`
- Read: `backend/src/services/canvas.py`
- Read: `../ai-movie-studio/frontend/src/components/canvas/CanvasAssistant.vue`
- Read: `../ai-movie-studio/frontend/src/components/canvas/assistant/*`
- Read: `../ai-movie-studio/frontend/src/utils/assistantRichText.js`

## Chunk 1: Backend Contract And Session Foundations

### Task 1: Add LangGraph dependency and assistant API schemas

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/src/api/schemas/canvas_assistant.py`
- Modify: `backend/src/api/schemas/__init__.py`

- [ ] **Step 1: Write the failing schema/API import test**

```python
def test_canvas_assistant_schema_imports() -> None:
    from src.api.schemas.canvas_assistant import CanvasAssistantChatRequest

    assert CanvasAssistantChatRequest.model_fields["message"].is_required()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/unit/test_canvas_assistant_service.py -q -k schema_imports`
Expected: FAIL because `canvas_assistant` schema module does not exist.

- [ ] **Step 3: Add `langgraph` dependency and define assistant request/response models**

```python
class CanvasAssistantChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    selected_item_ids: list[str] = Field(default_factory=list)


class CanvasAssistantResumeRequest(BaseModel):
    session_id: str
    confirmation_id: str
    approved: bool
    selected_model: str | None = None
```

- [ ] **Step 4: Run the focused test to verify it passes**

Run: `pytest backend/tests/unit/test_canvas_assistant_service.py -q -k schema_imports`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/src/api/schemas/canvas_assistant.py backend/src/api/schemas/__init__.py backend/tests/unit/test_canvas_assistant_service.py
git commit -m "feat: add canvas assistant API schemas"
```

### Task 2: Create session store for assistant conversation and confirmation resume

**Files:**
- Create: `backend/src/assistant/types.py`
- Create: `backend/src/assistant/session_store.py`
- Test: `backend/tests/unit/test_canvas_assistant_session_store.py`

- [ ] **Step 1: Write failing tests for session lifecycle**

```python
async def test_session_store_creates_and_returns_session() -> None:
    store = InMemoryCanvasAssistantSessionStore()

    session = await store.get_or_create("session-1", "user-1", "doc-1")

    assert session.session_id == "session-1"
    assert session.pending_confirmation is None


async def test_session_store_persists_pending_confirmation() -> None:
    store = InMemoryCanvasAssistantSessionStore()
    session = await store.get_or_create("session-1", "user-1", "doc-1")
    session.pending_confirmation = PendingConfirmation(confirmation_id="c1", kind="apply_plan")

    await store.save(session)
    restored = await store.require("session-1", "user-1", "doc-1")

    assert restored.pending_confirmation.confirmation_id == "c1"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest backend/tests/unit/test_canvas_assistant_session_store.py -q`
Expected: FAIL because the store/types do not exist.

- [ ] **Step 3: Implement typed session models and in-memory store**

```python
@dataclass
class PendingConfirmation:
    confirmation_id: str
    kind: str
    title: str = ""
    message: str = ""
    items: list[dict[str, Any]] = field(default_factory=list)
    selected_model: str = ""
    model_options: list[str] = field(default_factory=list)
    plan_snapshot: dict[str, Any] = field(default_factory=dict)


@dataclass
class CanvasAssistantSession:
    session_id: str
    user_id: str
    document_id: str
    messages: list[dict[str, str]] = field(default_factory=list)
    summary: str = ""
    pending_confirmation: PendingConfirmation | None = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest backend/tests/unit/test_canvas_assistant_session_store.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/assistant/types.py backend/src/assistant/session_store.py backend/tests/unit/test_canvas_assistant_session_store.py
git commit -m "feat: add canvas assistant session store"
```

### Task 3: Define SSE event writer and API envelope

**Files:**
- Create: `backend/src/assistant/sse.py`
- Test: `backend/tests/unit/test_canvas_assistant_service.py`

- [ ] **Step 1: Write the failing SSE formatting test**

```python
def test_sse_event_writer_serializes_event() -> None:
    body = encode_sse_event("message", {"delta": "hello"})
    assert body == 'data: {"type":"message","data":{"delta":"hello"}}\\n\\n'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/unit/test_canvas_assistant_service.py -q -k sse_event_writer`
Expected: FAIL because `encode_sse_event` does not exist.

- [ ] **Step 3: Implement stable event encoding helpers**

```python
def encode_sse_event(event_type: str, payload: Any) -> str:
    body = json.dumps({"type": event_type, "data": payload}, ensure_ascii=False, separators=(",", ":"))
    return f"data: {body}\\n\\n"
```

- [ ] **Step 4: Run the focused test to verify it passes**

Run: `pytest backend/tests/unit/test_canvas_assistant_service.py -q -k sse_event_writer`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/assistant/sse.py backend/tests/unit/test_canvas_assistant_service.py
git commit -m "feat: add canvas assistant sse helpers"
```

## Chunk 2: Tool Layer And Plan Validation

### Task 4: Add thin canvas tools that wrap existing services

**Files:**
- Create: `backend/src/assistant/tools/canvas_tools.py`
- Test: `backend/tests/unit/test_canvas_assistant_tools.py`

- [ ] **Step 1: Write failing tests for snapshot/create/update/connect helpers**

```python
async def test_get_canvas_snapshot_returns_document_items_and_connections() -> None:
    service = FakeCanvasService()
    tools = CanvasAssistantCanvasTools(service=service, generation_service=None)

    snapshot = await tools.get_canvas_snapshot(document_id="doc-1", user_id="user-1")

    assert snapshot["document"]["id"] == "doc-1"
    assert snapshot["items"] == service.items
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest backend/tests/unit/test_canvas_assistant_tools.py -q -k snapshot`
Expected: FAIL because the tool module does not exist.

- [ ] **Step 3: Implement tool wrappers over `CanvasService`**

```python
class CanvasAssistantCanvasTools:
    async def get_canvas_snapshot(self, document_id: str, user_id: str, item_ids: list[str] | None = None) -> dict[str, Any]:
        graph = await self.service.get_graph(document_id, user_id)
        ...

    async def create_canvas_items(...): ...
    async def update_canvas_items(...): ...
    async def connect_canvas_items(...): ...
```

- [ ] **Step 4: Run the focused tool tests to verify they pass**

Run: `pytest backend/tests/unit/test_canvas_assistant_tools.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/assistant/tools/canvas_tools.py backend/tests/unit/test_canvas_assistant_tools.py
git commit -m "feat: add canvas assistant canvas tools"
```

### Task 5: Add generation submission tool for image/video workflows

**Files:**
- Create: `backend/src/assistant/tools/generation_tools.py`
- Test: `backend/tests/unit/test_canvas_assistant_tools.py`

- [ ] **Step 1: Write failing tests for generation dispatch**

```python
async def test_submit_generation_tasks_dispatches_image_generation() -> None:
    generation_service = FakeGenerationService()
    tools = CanvasAssistantGenerationTools(generation_service)

    result = await tools.submit_generation_tasks(
        user_id="user-1",
        requests=[{"item_id": "item-1", "kind": "image", "payload": {"prompt": "x"}}],
    )

    assert result["submitted"][0]["item_id"] == "item-1"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest backend/tests/unit/test_canvas_assistant_tools.py -q -k submit_generation_tasks`
Expected: FAIL because the generation tool does not exist.

- [ ] **Step 3: Implement generation tool that reuses `CanvasGenerationService`**

```python
class CanvasAssistantGenerationTools:
    async def submit_generation_tasks(self, user_id: str, requests: list[dict[str, Any]]) -> dict[str, Any]:
        ...
```

- [ ] **Step 4: Run the focused tests to verify they pass**

Run: `pytest backend/tests/unit/test_canvas_assistant_tools.py -q -k submit_generation_tasks`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/assistant/tools/generation_tools.py backend/tests/unit/test_canvas_assistant_tools.py
git commit -m "feat: add canvas assistant generation tools"
```

### Task 6: Add plan schema and validator for safe create/update/connect actions

**Files:**
- Create: `backend/src/assistant/plans.py`
- Test: `backend/tests/unit/test_canvas_assistant_plans.py`

- [ ] **Step 1: Write failing tests for plan validation**

```python
def test_validate_update_plan_rejects_missing_item_id() -> None:
    with pytest.raises(ValueError):
        validate_assistant_plan({"actions": [{"type": "update_item", "patch": {"title": "x"}}]})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest backend/tests/unit/test_canvas_assistant_plans.py -q`
Expected: FAIL because the validator does not exist.

- [ ] **Step 3: Implement strict plan models and validation**

```python
class UpdateItemAction(BaseModel):
    type: Literal["update_item"]
    item_id: str
    patch: dict[str, Any]


class CreateItemsAction(BaseModel):
    type: Literal["create_items"]
    items: list[dict[str, Any]]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest backend/tests/unit/test_canvas_assistant_plans.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/assistant/plans.py backend/tests/unit/test_canvas_assistant_plans.py
git commit -m "feat: add canvas assistant plan validator"
```

## Chunk 3: LangGraph Orchestration

### Task 7: Define assistant state and graph routing

**Files:**
- Create: `backend/src/assistant/graph/state.py`
- Create: `backend/src/assistant/graph/router.py`
- Test: `backend/tests/unit/test_canvas_assistant_service.py`

- [ ] **Step 1: Write failing tests for route decisions**

```python
def test_route_after_plan_goes_to_confirmation_when_needed() -> None:
    state = AssistantGraphState(action_plan={"requires_confirmation": True})
    assert route_after_plan(state) == "confirm_gate"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest backend/tests/unit/test_canvas_assistant_service.py -q -k route_after_plan`
Expected: FAIL because state/router modules do not exist.

- [ ] **Step 3: Implement graph state model and router helpers**

```python
class AssistantGraphState(TypedDict, total=False):
    session_id: str
    user_id: str
    document_id: str
    user_message: str
    snapshot: dict[str, Any]
    action_plan: dict[str, Any]
    execution_result: dict[str, Any]
```

- [ ] **Step 4: Run the focused tests to verify they pass**

Run: `pytest backend/tests/unit/test_canvas_assistant_service.py -q -k route_after_plan`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/assistant/graph/state.py backend/src/assistant/graph/router.py backend/tests/unit/test_canvas_assistant_service.py
git commit -m "feat: add assistant graph state and routing"
```

### Task 8: Implement LangGraph nodes for load, reason, confirm, execute, summarize

**Files:**
- Create: `backend/src/assistant/prompts.py`
- Create: `backend/src/assistant/graph/nodes.py`
- Create: `backend/src/assistant/graph/builder.py`
- Test: `backend/tests/unit/test_canvas_assistant_service.py`

- [ ] **Step 1: Write failing tests for three primary scenarios**

```python
async def test_reason_node_marks_script_request_as_needing_clarification() -> None:
    ...


async def test_execute_node_applies_update_actions() -> None:
    ...


async def test_confirm_node_returns_pending_confirmation_payload() -> None:
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest backend/tests/unit/test_canvas_assistant_service.py -q -k "script_request or applies_update or pending_confirmation"`
Expected: FAIL because nodes are not implemented.

- [ ] **Step 3: Implement graph nodes with explicit responsibilities**

```python
async def load_context_node(state: AssistantGraphState, deps: AssistantDeps) -> AssistantGraphState: ...
async def reason_intent_node(state: AssistantGraphState, deps: AssistantDeps) -> AssistantGraphState: ...
async def confirm_gate_node(state: AssistantGraphState, deps: AssistantDeps) -> AssistantGraphState: ...
async def execute_plan_node(state: AssistantGraphState, deps: AssistantDeps) -> AssistantGraphState: ...
async def summarize_result_node(state: AssistantGraphState, deps: AssistantDeps) -> AssistantGraphState: ...
```

- [ ] **Step 4: Run the focused tests to verify they pass**

Run: `pytest backend/tests/unit/test_canvas_assistant_service.py -q -k "script_request or applies_update or pending_confirmation"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/assistant/prompts.py backend/src/assistant/graph/nodes.py backend/src/assistant/graph/builder.py backend/tests/unit/test_canvas_assistant_service.py
git commit -m "feat: add canvas assistant langgraph nodes"
```

### Task 9: Add assistant service to stream events and handle resume

**Files:**
- Create: `backend/src/assistant/service.py`
- Test: `backend/tests/unit/test_canvas_assistant_service.py`

- [ ] **Step 1: Write failing service tests for chat and resume**

```python
async def test_chat_stream_emits_confirmation_event_when_plan_requires_approval() -> None:
    ...


async def test_resume_executes_saved_plan_when_confirmation_is_approved() -> None:
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest backend/tests/unit/test_canvas_assistant_service.py -q`
Expected: FAIL because the service does not exist.

- [ ] **Step 3: Implement assistant service over LangGraph graph + session store**

```python
class CanvasAssistantService:
    async def stream_chat(...): ...
    async def stream_resume(...): ...
```

- [ ] **Step 4: Run unit tests to verify they pass**

Run: `pytest backend/tests/unit/test_canvas_assistant_service.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/assistant/service.py backend/tests/unit/test_canvas_assistant_service.py
git commit -m "feat: add canvas assistant service"
```

## Chunk 4: FastAPI Integration

### Task 10: Expose `/canvas-assistant/chat` and `/canvas-assistant/resume` endpoints

**Files:**
- Create: `backend/src/api/v1/canvas_assistant.py`
- Modify: `backend/src/api/v1/__init__.py`
- Test: `backend/tests/integration/test_canvas_assistant_api.py`

- [ ] **Step 1: Write failing integration tests for chat and resume routes**

```python
async def test_canvas_assistant_chat_route_streams_sse_events(async_client, auth_headers) -> None:
    response = await async_client.post(
        "/api/v1/canvas-assistant/chat",
        json={"message": "生成一个剧本"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest backend/tests/integration/test_canvas_assistant_api.py -q`
Expected: FAIL because the route does not exist.

- [ ] **Step 3: Implement FastAPI routes and wire dependencies**

```python
@router.post("/canvas-assistant/chat")
async def chat_canvas_assistant(...):
    return StreamingResponse(...)


@router.post("/canvas-assistant/resume")
async def resume_canvas_assistant(...):
    return StreamingResponse(...)
```

- [ ] **Step 4: Run integration tests to verify they pass**

Run: `pytest backend/tests/integration/test_canvas_assistant_api.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/api/v1/canvas_assistant.py backend/src/api/v1/__init__.py backend/tests/integration/test_canvas_assistant_api.py
git commit -m "feat: expose canvas assistant api routes"
```

## Chunk 5: Frontend Assistant Rail

### Task 11: Add frontend assistant service and timeline mapping composables

**Files:**
- Create: `frontend/src/services/canvasAssistant.js`
- Create: `frontend/src/composables/useCanvasAssistant.js`
- Create: `frontend/src/composables/useCanvasAssistantTimeline.js`
- Test: `frontend/src/tests/unit/services/canvasAssistant.test.js`
- Test: `frontend/src/tests/unit/composables/useCanvasAssistantTimeline.test.js`

- [ ] **Step 1: Write failing frontend tests for SSE parsing and timeline mapping**

```javascript
it('parses confirmation events into pending confirmation state', async () => {
  ...
})

it('maps messages and tool events into timeline items', () => {
  ...
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cmd /c "cd /d D:\\code\\movie\\aicon\\frontend && npm run test -- src/tests/unit/services/canvasAssistant.test.js src/tests/unit/composables/useCanvasAssistantTimeline.test.js"`
Expected: FAIL because the modules do not exist.

- [ ] **Step 3: Implement service/composables**

```javascript
export function useCanvasAssistant(documentId, options = {}) {
  const messages = ref([])
  const toolCalls = ref([])
  const pendingConfirmation = ref(null)
  ...
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cmd /c "cd /d D:\\code\\movie\\aicon\\frontend && npm run test -- src/tests/unit/services/canvasAssistant.test.js src/tests/unit/composables/useCanvasAssistantTimeline.test.js"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/services/canvasAssistant.js frontend/src/composables/useCanvasAssistant.js frontend/src/composables/useCanvasAssistantTimeline.js frontend/src/tests/unit/services/canvasAssistant.test.js frontend/src/tests/unit/composables/useCanvasAssistantTimeline.test.js
git commit -m "feat: add frontend canvas assistant state"
```

### Task 12: Port assistant UI components and adapt them to `aicon`

**Files:**
- Create: `frontend/src/components/canvas/CanvasAssistant.vue`
- Create: `frontend/src/components/canvas/assistant/CanvasAssistantHeader.vue`
- Create: `frontend/src/components/canvas/assistant/CanvasAssistantTimeline.vue`
- Create: `frontend/src/components/canvas/assistant/CanvasAssistantMessageItem.vue`
- Create: `frontend/src/components/canvas/assistant/CanvasAssistantComposer.vue`
- Create: `frontend/src/components/canvas/assistant/CanvasAssistantConfirmationCard.vue`
- Create: `frontend/src/components/canvas/assistant/CanvasAssistantToolSummary.vue`

- [ ] **Step 1: Write a failing component smoke test**

```javascript
it('renders pending confirmation inside the assistant timeline', () => {
  ...
})
```

- [ ] **Step 2: Run the component test to verify it fails**

Run: `cmd /c "cd /d D:\\code\\movie\\aicon\\frontend && npm run test -- src/tests/unit/components/canvas/CanvasAssistant.test.js"`
Expected: FAIL because the component does not exist.

- [ ] **Step 3: Port UI structure from the old assistant and adapt prop/event names**

```vue
<CanvasAssistantTimeline
  :items="timelineItems"
  :pending-confirmation="pendingConfirmation"
  ...
/>
```

- [ ] **Step 4: Run the component test to verify it passes**

Run: `cmd /c "cd /d D:\\code\\movie\\aicon\\frontend && npm run test -- src/tests/unit/components/canvas/CanvasAssistant.test.js"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/canvas/CanvasAssistant.vue frontend/src/components/canvas/assistant frontend/src/tests/unit/components/canvas/CanvasAssistant.test.js
git commit -m "feat: port canvas assistant ui"
```

### Task 13: Mount assistant into canvas editor and bind selected-node context

**Files:**
- Modify: `frontend/src/views/canvas/CanvasEditor.vue`

- [ ] **Step 1: Write a failing editor integration test or targeted assertion**

```javascript
it('mounts canvas assistant inside canvas editor', () => {
  ...
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cmd /c "cd /d D:\\code\\movie\\aicon\\frontend && npm run test -- src/tests/unit/views/canvas/CanvasEditorAssistant.test.js"`
Expected: FAIL because the editor does not render the assistant.

- [ ] **Step 3: Mount the assistant and wire `documentId`, `selectedItem`, and resume/send handlers**

```vue
<CanvasAssistant
  :document-id="document?.id || ''"
  :selected-item="selectedItem"
  :selected-item-ids="selectedItemIds"
  @focus-item="handleFocusItem"
/>
```

- [ ] **Step 4: Run the targeted test to verify it passes**

Run: `cmd /c "cd /d D:\\code\\movie\\aicon\\frontend && npm run test -- src/tests/unit/views/canvas/CanvasEditorAssistant.test.js"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/canvas/CanvasEditor.vue frontend/src/tests/unit/views/canvas/CanvasEditorAssistant.test.js
git commit -m "feat: embed canvas assistant into editor"
```

## Chunk 6: Scenario-Focused Verification

### Task 14: Verify script generation clarification flow

**Files:**
- Modify: `backend/tests/integration/test_canvas_assistant_api.py`
- Modify: `frontend/src/tests/unit/composables/useCanvasAssistantTimeline.test.js`

- [ ] **Step 1: Add failing end-to-end-ish tests for `"生成一个剧本"`**

```python
async def test_script_generation_request_returns_clarifying_question(...) -> None:
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest backend/tests/integration/test_canvas_assistant_api.py -q -k script_generation`
Expected: FAIL because the graph does not yet steer into clarification.

- [ ] **Step 3: Adjust prompts/planner until the scenario passes**

```python
# Prompt contract:
# - When user asks to generate a script with insufficient constraints,
#   ask for the minimum next detail instead of creating nodes immediately.
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest backend/tests/integration/test_canvas_assistant_api.py -q -k script_generation`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/integration/test_canvas_assistant_api.py frontend/src/tests/unit/composables/useCanvasAssistantTimeline.test.js backend/src/assistant/prompts.py
git commit -m "test: cover script clarification flow"
```

### Task 15: Verify node extraction flow from existing source nodes

**Files:**
- Modify: `backend/tests/integration/test_canvas_assistant_api.py`
- Modify: `backend/tests/unit/test_canvas_assistant_service.py`

- [ ] **Step 1: Add failing tests for extraction into single and multiple nodes**

```python
async def test_extract_request_creates_multiple_storyboard_nodes_from_script(...) -> None:
    ...


async def test_extract_request_can_create_single_derived_node(...) -> None:
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest backend/tests/integration/test_canvas_assistant_api.py -q -k extract_request`
Expected: FAIL before planner/executor support is complete.

- [ ] **Step 3: Implement or refine derive/create/connect planning logic**

```python
# Planner must emit create_items + connect_items actions
# from source node content and requested target shape.
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest backend/tests/integration/test_canvas_assistant_api.py -q -k extract_request`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/integration/test_canvas_assistant_api.py backend/tests/unit/test_canvas_assistant_service.py backend/src/assistant/graph/nodes.py
git commit -m "test: cover canvas extraction flows"
```

### Task 16: Verify prompt optimization and reference update flow

**Files:**
- Modify: `backend/tests/integration/test_canvas_assistant_api.py`
- Modify: `backend/tests/unit/test_canvas_assistant_plans.py`

- [ ] **Step 1: Add failing tests for prompt patch and mention/reference updates**

```python
async def test_revise_request_updates_existing_prompt_without_overwriting_unrelated_fields(...) -> None:
    ...


async def test_update_reference_request_rewrites_prompt_tokens_and_mentions(...) -> None:
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest backend/tests/integration/test_canvas_assistant_api.py -q -k "revise_request or update_reference"`
Expected: FAIL before patch semantics are complete.

- [ ] **Step 3: Refine patch builder and plan validator**

```python
# Update actions must only patch requested fields and preserve unrelated content keys.
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest backend/tests/integration/test_canvas_assistant_api.py -q -k "revise_request or update_reference"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/integration/test_canvas_assistant_api.py backend/tests/unit/test_canvas_assistant_plans.py backend/src/assistant/plans.py backend/src/assistant/graph/nodes.py
git commit -m "test: cover prompt revision and reference updates"
```

## Final Verification

- [ ] **Step 1: Run backend unit tests**

Run: `pytest backend/tests/unit/test_canvas_assistant_*.py -q`
Expected: PASS.

- [ ] **Step 2: Run backend integration tests**

Run: `pytest backend/tests/integration/test_canvas_assistant_api.py -q`
Expected: PASS.

- [ ] **Step 3: Run frontend unit tests for assistant**

Run: `cmd /c "cd /d D:\\code\\movie\\aicon\\frontend && npm run test -- src/tests/unit/services/canvasAssistant.test.js src/tests/unit/composables/useCanvasAssistantTimeline.test.js src/tests/unit/components/canvas/CanvasAssistant.test.js src/tests/unit/views/canvas/CanvasEditorAssistant.test.js"`
Expected: PASS.

- [ ] **Step 4: Run frontend production build**

Run: `cmd /c "cd /d D:\\code\\movie\\aicon\\frontend && npm run build"`
Expected: PASS.

- [ ] **Step 5: Manual verification**

Run through:
- Ask assistant `生成一个剧本` and confirm it asks a targeted follow-up question.
- Ask assistant to derive nodes from one selected text node and verify new nodes + connections appear.
- Ask assistant to optimize one or more prompts and verify only intended fields change.
- Ask assistant to update image/text references and verify `promptTokens` / resolved mentions stay coherent.

- [ ] **Step 6: Commit**

```bash
git add backend frontend
git commit -m "feat: migrate canvas assistant to aicon with langgraph"
```

## Notes For Execution

- Keep LangGraph focused on orchestration. Do not push canvas CRUD logic into graph nodes.
- Avoid introducing monolithic "do everything" tools for script generation, extraction, or prompt revision. Use LLM planning + thin tools.
- Confirmation/resume must execute a frozen plan snapshot, not rerun planner inference after approval.
- Preserve `aicon` existing canvas/generation semantics unless a specific assistant behavior requires a minimal extension.
- When updating node content, always apply partial patches and preserve unrelated `content` / `generation_config` keys.

Plan complete and saved to `docs/superpowers/plans/2026-04-03-canvas-assistant-langgraph-migration.md`. Ready to execute?
