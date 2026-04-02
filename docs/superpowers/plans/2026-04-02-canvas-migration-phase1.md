# Canvas Migration Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the independent canvas in `aicon` from the current graph-demo flow to a usable workbench flow with snapshot/item APIs, node editing, text SSE generation, and basic image/video generation result writeback.

**Architecture:** Keep `aicon`'s independent `/canvas` entry and backend storage/provider/task infrastructure, but replace the current graph-centric frontend/backend interaction with a split workbench model: lite stage snapshot for the board, item detail/patch for studios, and generation adapters that accept old-canvas prompt semantics while executing on `aicon` providers. History, assistant, chapter bindings, and billing are explicitly out of scope.

**Tech Stack:** FastAPI, SQLAlchemy async, Celery, Vue 3, Element Plus, Konva, Vitest, Pytest

---

## File Map

### Backend

- Modify: `backend/src/api/v1/canvas.py`
  - Add document lite snapshot mode, item CRUD, preview patch, connection CRUD, canvas-scoped generation endpoints, and task query/upload endpoints.
- Modify: `backend/src/api/schemas/canvas.py`
  - Add stage snapshot, item patch, preview patch, generation request, task status, and upload response schemas.
- Modify: `backend/src/services/canvas.py`
  - Split graph persistence concerns from workbench concerns; add snapshot projection, item patch/create/delete, preview resolution, and generation request normalization.
- Modify: `backend/src/tasks/canvas.py`
  - Extend task handling if text SSE and video polling require additional helper hooks.
- Create or modify: `backend/tests/integration/test_canvas_api.py`
  - Cover snapshot/item/connection endpoints and generation endpoint contracts.

### Frontend

- Modify: `frontend/src/services/canvas.js`
  - Replace graph-first service usage with snapshot/item/connection/generation endpoints.
- Create: `frontend/src/composables/useCanvasSnapshotState.js`
  - Load lite snapshot, maintain stage items/connections, and update local projection from item patches.
- Create: `frontend/src/composables/useCanvasNodeEditor.js`
  - Resolve selected item details and submit node-level patch mutations.
- Create: `frontend/src/composables/useCanvasTextGeneration.js`
  - Manage text generation submit + SSE stream updates.
- Create: `frontend/src/composables/useCanvasImageGeneration.js`
  - Manage image generation submit + completion sync.
- Create: `frontend/src/composables/useCanvasVideoEditor.js`
  - Manage video generation submit, task polling, and upload fallback.
- Create: `frontend/src/composables/useCanvasPreviewLoader.js`
  - Load visible media previews on demand.
- Modify: `frontend/src/views/canvas/CanvasEditor.vue`
  - Rewire page orchestration to snapshot/detail/generation composables.
- Modify: `frontend/src/components/canvas/CanvasTextStudio.vue`
  - Align emits/props with item-detail and streaming text workflow.
- Modify: `frontend/src/components/canvas/CanvasImageStudio.vue`
  - Align emits/props with style reference + async result writeback.
- Modify: `frontend/src/components/canvas/CanvasVideoStudio.vue`
  - Align emits/props with generation config, task status, and upload fallback.
- Modify: `frontend/src/components/canvas/KonvaCanvasStage.vue`
  - Ensure stage uses snapshot-safe item fields and preview updates.
- Modify: `frontend/src/utils/promptMentionTokens.js`
  - Ensure prompt token derivation matches backend request contract.

### Tests

- Modify or create: `frontend/src/components/canvas/*.test.js`
  - Add targeted tests only if an edited component already has nearby tests.
- Modify or create: `frontend/src/composables/*.test.js`
  - Add focused tests for token normalization or generation state if feasible.

## Chunk 1: Backend Workbench APIs

### Task 1: Add failing integration tests for lite snapshot and item CRUD

**Files:**
- Modify: `backend/tests/integration/test_canvas_api.py`

- [ ] **Step 1: Write the failing test**

Add tests for:
- `GET /api/v1/canvas-documents/{id}?mode=lite`
- `POST /api/v1/canvas-documents/{id}/items`
- `GET /api/v1/canvas-documents/{id}/items/{itemId}`
- `PATCH /api/v1/canvas-documents/{id}/items/{itemId}`
- `DELETE /api/v1/canvas-documents/{id}/items/{itemId}`

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
cd backend && pytest tests/integration/test_canvas_api.py -k "lite or item" -v
```

Expected:
- Fail with `404`/missing route or schema mismatch.

- [ ] **Step 3: Write minimal implementation**

Implement schema and route stubs in:
- `backend/src/api/schemas/canvas.py`
- `backend/src/api/v1/canvas.py`
- `backend/src/services/canvas.py`

Behavior:
- lite snapshot returns document + projected items + projected connections
- item CRUD persists against existing `canvas_items`

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
cd backend && pytest tests/integration/test_canvas_api.py -k "lite or item" -v
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/api/schemas/canvas.py backend/src/api/v1/canvas.py backend/src/services/canvas.py backend/tests/integration/test_canvas_api.py
git commit -m "feat: add canvas snapshot and item APIs"
```

### Task 2: Add failing integration tests for connection CRUD and preview patches

**Files:**
- Modify: `backend/tests/integration/test_canvas_api.py`

- [ ] **Step 1: Write the failing test**

Add tests for:
- `POST /api/v1/canvas-documents/{id}/connections`
- `DELETE /api/v1/canvas-documents/{id}/connections/{connectionId}`
- `POST /api/v1/canvas-documents/{id}/items/previews`

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
cd backend && pytest tests/integration/test_canvas_api.py -k "connection or preview" -v
```

Expected:
- Fail because routes do not exist or payload shape is wrong.

- [ ] **Step 3: Write minimal implementation**

Implement connection and preview flows in:
- `backend/src/api/schemas/canvas.py`
- `backend/src/api/v1/canvas.py`
- `backend/src/services/canvas.py`

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
cd backend && pytest tests/integration/test_canvas_api.py -k "connection or preview" -v
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/api/schemas/canvas.py backend/src/api/v1/canvas.py backend/src/services/canvas.py backend/tests/integration/test_canvas_api.py
git commit -m "feat: add canvas connection and preview APIs"
```

## Chunk 2: Backend Generation Contracts

### Task 3: Add failing tests for text/image/video generation endpoint contracts

**Files:**
- Modify: `backend/tests/integration/test_canvas_api.py`
- Modify: `backend/src/api/schemas/canvas.py`

- [ ] **Step 1: Write the failing test**

Adjust generation tests to assert first-phase contract:
- text accepts structured prompt fields and returns task/generation payload suitable for SSE-driven UI
- image accepts prompt tokens/resolved mentions/style reference fields
- video accepts prompt tokens/resolved mentions/generation config

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
cd backend && pytest tests/integration/test_canvas_api.py -k "generate_text or generate_image or generate_video" -v
```

Expected:
- Fail on request validation or missing fields.

- [ ] **Step 3: Write minimal implementation**

Update:
- `backend/src/api/schemas/canvas.py`
- `backend/src/api/v1/canvas.py`
- `backend/src/services/canvas.py`
- `backend/src/tasks/canvas.py`

Keep:
- provider/task/storage stack

Drop:
- billing assumptions in canvas-specific behavior

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
cd backend && pytest tests/integration/test_canvas_api.py -k "generate_text or generate_image or generate_video" -v
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/api/schemas/canvas.py backend/src/api/v1/canvas.py backend/src/services/canvas.py backend/src/tasks/canvas.py backend/tests/integration/test_canvas_api.py
git commit -m "feat: adapt canvas generation contracts"
```

### Task 4: Add failing tests for video task query and upload fallback

**Files:**
- Modify: `backend/tests/integration/test_canvas_api.py`

- [ ] **Step 1: Write the failing test**

Add tests for:
- `GET /api/v1/canvas-documents/{id}/items/{itemId}/video-tasks/{taskId}`
- `POST /api/v1/canvas-documents/{id}/items/{itemId}/upload-video`

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
cd backend && pytest tests/integration/test_canvas_api.py -k "video task or upload video" -v
```

Expected:
- Fail because route/response is missing.

- [ ] **Step 3: Write minimal implementation**

Update:
- `backend/src/api/schemas/canvas.py`
- `backend/src/api/v1/canvas.py`
- `backend/src/services/canvas.py`

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
cd backend && pytest tests/integration/test_canvas_api.py -k "video task or upload video" -v
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/api/schemas/canvas.py backend/src/api/v1/canvas.py backend/src/services/canvas.py backend/tests/integration/test_canvas_api.py
git commit -m "feat: add canvas video task and upload endpoints"
```

## Chunk 3: Frontend Snapshot and Node Editing

### Task 5: Add failing frontend test or minimal harness coverage for snapshot service contract

**Files:**
- Modify: `frontend/src/services/canvas.js`
- Optional Test: `frontend/src/composables/useCanvasEditor.test.js` or create a focused composable test if practical

- [ ] **Step 1: Write the failing test**

If feasible, add a focused test for snapshot/item endpoint mapping. If not, define this task as API-layer contract verification during manual run and keep automated coverage in backend.

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
cd frontend && npm run test:run -- --passWithNoTests
```

Expected:
- Targeted test fails, or there is no test harness and this step is recorded as not applicable.

- [ ] **Step 3: Write minimal implementation**

Implement service methods in:
- `frontend/src/services/canvas.js`

Methods:
- `getLiteDocument`
- `createItem`
- `getItem`
- `updateItem`
- `deleteItem`
- `getItemPreviews`
- `createConnection`
- `deleteConnection`
- generation/task/upload methods under document scope

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
cd frontend && npm run test:run -- --passWithNoTests
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/services/canvas.js
git commit -m "feat: align canvas frontend service with workbench APIs"
```

### Task 6: Replace graph-centric editor state with snapshot/detail composables

**Files:**
- Create: `frontend/src/composables/useCanvasSnapshotState.js`
- Create: `frontend/src/composables/useCanvasNodeEditor.js`
- Create: `frontend/src/composables/useCanvasPreviewLoader.js`
- Modify: `frontend/src/views/canvas/CanvasEditor.vue`

- [ ] **Step 1: Write the failing test**

Prefer a small composable test if practical. Otherwise use manual red step:
- editor no longer loads from `getGraph`
- selection triggers detail fetch
- node patch updates stage state

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
cd frontend && npm run build
```

Expected:
- Fails while new composables/wiring are incomplete.

- [ ] **Step 3: Write minimal implementation**

Implement:
- snapshot loading and normalization
- selected item detail loading
- local snapshot patch reconciliation
- stage preview loading hook

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
cd frontend && npm run build
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/composables/useCanvasSnapshotState.js frontend/src/composables/useCanvasNodeEditor.js frontend/src/composables/useCanvasPreviewLoader.js frontend/src/views/canvas/CanvasEditor.vue
git commit -m "feat: migrate canvas editor to snapshot detail flow"
```

## Chunk 4: Text Generation and Studios

### Task 7: Add failing test for text generation composable contract

**Files:**
- Create: `frontend/src/composables/useCanvasTextGeneration.js`
- Modify: `frontend/src/components/canvas/CanvasTextStudio.vue`
- Modify: `frontend/src/views/canvas/CanvasEditor.vue`

- [ ] **Step 1: Write the failing test**

Add a focused composable/unit test if practical for:
- submit generation request
- consume text delta updates
- finalize node content on complete

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
cd frontend && npm run test:run -- useCanvasTextGeneration
```

Expected:
- FAIL

- [ ] **Step 3: Write minimal implementation**

Implement:
- text generation submit
- SSE or event stream handling
- node content update hooks
- studio prop/emit alignment

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
cd frontend && npm run test:run -- useCanvasTextGeneration
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/composables/useCanvasTextGeneration.js frontend/src/components/canvas/CanvasTextStudio.vue frontend/src/views/canvas/CanvasEditor.vue
git commit -m "feat: add canvas text streaming workflow"
```

## Chunk 5: Image and Video Generation

### Task 8: Add image generation adapter and studio wiring

**Files:**
- Create: `frontend/src/composables/useCanvasImageGeneration.js`
- Modify: `frontend/src/components/canvas/CanvasImageStudio.vue`
- Modify: `frontend/src/views/canvas/CanvasEditor.vue`
- Modify: `frontend/src/utils/promptMentionTokens.js`

- [ ] **Step 1: Write the failing test**

Add a targeted test if practical for prompt token normalization and image request assembly.

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
cd frontend && npm run test:run -- promptMentionTokens
```

Expected:
- FAIL

- [ ] **Step 3: Write minimal implementation**

Implement:
- image request assembly from prompt tokens and mentions
- optional style reference fields
- async result writeback

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
cd frontend && npm run test:run -- promptMentionTokens
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/composables/useCanvasImageGeneration.js frontend/src/components/canvas/CanvasImageStudio.vue frontend/src/views/canvas/CanvasEditor.vue frontend/src/utils/promptMentionTokens.js
git commit -m "feat: add canvas image generation adapter"
```

### Task 9: Add video generation adapter, task polling, and upload fallback

**Files:**
- Create or modify: `frontend/src/composables/useCanvasVideoEditor.js`
- Modify: `frontend/src/components/canvas/CanvasVideoStudio.vue`
- Modify: `frontend/src/views/canvas/CanvasEditor.vue`

- [ ] **Step 1: Write the failing test**

Add a focused unit test if practical for task polling state transitions, otherwise use build/manual verification.

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
cd frontend && npm run build
```

Expected:
- FAIL while video adapter wiring is incomplete.

- [ ] **Step 3: Write minimal implementation**

Implement:
- video generation submit
- task status polling
- node result preview writeback
- upload fallback

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
cd frontend && npm run build
```

Expected:
- PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/composables/useCanvasVideoEditor.js frontend/src/components/canvas/CanvasVideoStudio.vue frontend/src/views/canvas/CanvasEditor.vue
git commit -m "feat: add canvas video generation workflow"
```

## Final Verification

### Task 10: Run full verification

**Files:**
- No code changes

- [ ] **Step 1: Run backend integration tests**

Run:
```bash
cd backend && pytest tests/integration/test_canvas_api.py -v
```

Expected:
- PASS

- [ ] **Step 2: Run frontend build**

Run:
```bash
cd frontend && npm run build
```

Expected:
- PASS

- [ ] **Step 3: Run any targeted frontend tests added during implementation**

Run:
```bash
cd frontend && npm run test:run
```

Expected:
- PASS for targeted tests you introduced

- [ ] **Step 4: Commit final cleanup if needed**

```bash
git add <touched-files>
git commit -m "refactor: finish canvas migration phase 1"
```

Plan complete and saved to `docs/superpowers/plans/2026-04-02-canvas-migration-phase1.md`. Ready to execute.
