# Canvas 独立画布迁移设计

日期：2026-04-02

## 目标

把 `ai-movie-studio` 中除 assistant、章节入口、历史分支、计费分支外的画布主工作流迁移到 `aicon` 的独立画布入口：

- 保留 `aicon` 现有入口 `/canvas` 和 `/canvas/:canvasId`
- 完成文本、图片、视频节点的创建、编辑、连线、生成和结果回写
- 保留 `aicon` 当前本地部署可用的生成基础设施：provider、模型中心、任务队列、worker、存储
- 不迁移 assistant、章节绑定、历史抽屉/历史切换、计费与 credits

## 非目标

- 不迁移 Canvas Assistant
- 不迁移章节打开画布、章节导入画布
- 不做 generation history UI 和 history apply
- 不兼容旧项目的 billing、hold、capture、批次结算
- 不继续扩展 `graph save` 作为长期主链路

## 现状判断

### aicon 当前能力

- 有独立画布列表页和编辑页
- 有 Konva 舞台、文本/图片/视频 studio、prompt mention editor
- 后端已有 `canvas_documents`、`canvas_items`、`canvas_connections`、`canvas_item_generations`
- 已接入 provider factory、API Key、模型目录、Celery 任务、对象存储
- 当前主状态流仍是 `getGraph/saveGraph` 的整图读写模式
- 文本/图片/视频生成能力是简化版，缺少旧项目的完整画布工作台语义

### 旧项目可复用能力

- 轻量舞台快照和节点详情分离
- 节点级编辑状态管理
- prompt token / resolved mention 协议
- 文本流式生成
- 图片/视频节点更完整的输入组织和结果回写
- 媒体预览按需补拉
- 视频任务状态和上传兜底

### 关键差异

- `aicon` 生成链路依赖自己的 provider、任务、worker、system model 体系
- 旧项目的画布交互和生成输入协议更成熟，但其服务拆分不能直接照搬
- 因此迁移方式必须是：
  - 迁旧项目的画布交互和节点语义
  - 适配到 `aicon` 的生成执行基础设施

## 总体方案

采用“分层过渡”方案。

### 第一层：后端补齐主链路接口

在 `aicon` 的独立画布模型之上补齐旧项目需要的工作台接口，但不引入章节和 assistant 语义。

保留文档层接口：

- `GET /canvas-documents`
- `POST /canvas-documents`
- `GET /canvas-documents/:id`
- `PATCH /canvas-documents/:id`
- `DELETE /canvas-documents/:id`

新增或补齐工作台主链路接口：

- `GET /canvas-documents/:id?mode=lite`
- `POST /canvas-documents/:id/items`
- `GET /canvas-documents/:id/items/:itemId`
- `PATCH /canvas-documents/:id/items/:itemId`
- `DELETE /canvas-documents/:id/items/:itemId`
- `POST /canvas-documents/:id/items/previews`
- `POST /canvas-documents/:id/connections`
- `DELETE /canvas-documents/:id/connections/:connectionId`
- `POST /canvas-documents/:id/items/:itemId/generate-text`
- `POST /canvas-documents/:id/items/:itemId/generate-image`
- `POST /canvas-documents/:id/items/:itemId/generate-video`
- `GET /canvas-documents/:id/items/:itemId/video-tasks/:taskId`
- `POST /canvas-documents/:id/items/:itemId/upload-video`
- `GET /system/models/all`

兼容接口：

- `GET /canvas-documents/:id/graph`
- `PUT /canvas-documents/:id/graph`

这两个接口第一阶段保留，但不再作为新主链路中心。

### 第二层：前端切换到快照 + 节点详情模式

入口仍是 `frontend/src/views/canvas/CanvasEditor.vue`，但内部状态管理改为：

- 首屏拉取 lite snapshot
- 舞台只使用快照字段渲染
- 节点被选中时再拉 item detail
- 节点修改走 item patch
- 连线创建和删除走独立接口
- 文本、图片、视频生成分别走独立 composable

### 第三层：收敛旧的 graph 模式

- `useCanvasEditor` 不再承担长期的整图保存职责
- 当前 `useCanvasGeneration` 的统一轮询模型会拆开
- 文本、图片、视频各自回归自己的执行和回写逻辑

## 第一阶段范围

第一阶段只打通主工作流，不做历史和 assistant。

### 用户可见能力

- 新建独立画布
- 进入画布后加载节点与连线
- 创建文本、图片、视频节点
- 选中节点后打开对应 studio
- 编辑标题、正文、prompt、生成配置
- 拖动节点、创建连线、删除节点/连线
- 文本节点流式生成并写回
- 图片节点提交生成并写回结果
- 视频节点提交生成、查询任务状态、写回结果
- 图片/视频支持上传兜底结果

### 本阶段不做

- generation history drawer
- history select/apply
- 视频工作台
- reference material 入库
- assistant rail
- 章节来源导入

## 后端设计

### 数据模型策略

沿用 `aicon` 现有表：

- `canvas_documents`
- `canvas_items`
- `canvas_connections`
- `canvas_item_generations`

通过扩展 `content_json` 和 `generation_config_json` 承接旧项目节点语义，不引入旧项目 Go 侧整套表结构。

### 快照接口

`GET /canvas-documents/:id?mode=lite`

返回舞台首屏必要数据：

- document 基本信息
- items 的布局、标题、节点类型、舞台摘要内容
- connections

规则：

- 文本节点只返回摘要，不回整段正文
- 图片/视频节点只返回卡片渲染需要的轻量内容
- 离屏媒体节点不做全量预览签名

### 节点详情接口

`GET /canvas-documents/:id/items/:itemId`

返回当前节点完整编辑内容：

- 完整 content
- generation_config
- 当前任务状态摘要

### 节点更新接口

`PATCH /canvas-documents/:id/items/:itemId`

用于局部更新：

- 标题
- 位置和尺寸
- content
- generation_config

目标是替代整图保存。

### 生成适配原则

保留 `aicon` 的：

- provider factory
- SystemKey / model catalog
- 异步任务与 worker
- 存储服务

不保留：

- billing、hold、capture

生成适配层负责两件事：

1. 把旧项目前端的生成语义转换成 `aicon` 任务输入
- `prompt_tokens`
- `resolved_mentions`
- style reference
- video generation config

2. 把 `aicon` 任务执行结果写回成画布节点需要的内容结构
- 文本正文
- 图片结果 key/url
- 视频结果 key/url
- 当前任务摘要

### 文本生成

- 恢复旧项目风格的 SSE 事件流
- 事件类型保持文本开始、delta、完成、失败四段语义
- 前端文本 studio 直接消费流式内容

### 图片生成

- 异步任务执行
- 支持 prompt token / mention 解析
- 支持 style reference
- 结果写回 image 节点 content

### 视频生成

- 异步任务执行
- 支持 prompt token / mention 解析
- 支持 generation config
- 保留任务状态查询接口
- 保留上传兜底接口

## 前端设计

### 视图入口

保留：

- `frontend/src/views/canvas/CanvasList.vue`
- `frontend/src/views/canvas/CanvasEditor.vue`

### 状态拆分

将当前基于 graph 的状态流拆为：

- `useCanvasSnapshotState`
- `useCanvasTextEditor`
- `useCanvasImageEditor`
- `useCanvasVideoEditor`
- `useCanvasPreviewLoader`
- 文本/图片/视频生成 composable

不迁移：

- `useCanvasAssistant`
- `useCanvasHistoryPanel`

### 组件复用策略

优先复用或对齐旧项目这些组件和交互：

- `KonvaCanvasStage`
- `CanvasTextStudio`
- `CanvasImageStudio`
- `CanvasVideoStudio`
- `CanvasPromptMentionEditor`
- `CanvasWorkbenchLayout`
- `CanvasLinkCreateMenu`
- `CanvasConnectionActions`
- `CanvasLinkDragOverlay`

### 首屏加载链路

1. 打开 `CanvasEditor`
2. 拉取 lite snapshot
3. 渲染舞台
4. 视口内图片/视频节点按需补拉 preview
5. 选中节点时拉取 item detail
6. 打开对应 studio

### 保存链路

- 节点字段变更直接 patch 到 item 接口
- 连线单独 create/delete
- 不再依赖统一“保存画布”按钮作为主提交方式

### 生成链路

文本：

- 打开文本节点
- 提交结构化 prompt
- 订阅 SSE
- delta 回写编辑器和节点内容
- 完成后固化到 item

图片：

- 组织 prompt token、resolved mentions、style reference、model config
- 提交生成
- 轮询或按任务状态更新节点
- 结果回写到图片节点

视频：

- 组织 prompt token、resolved mentions、generation config
- 提交生成
- 轮询 task 状态
- 结果回写到视频节点
- 必要时允许上传视频兜底

## 实施顺序

### P1

- 补齐快照、节点详情、节点 patch、连线接口
- 前端切换到 lite snapshot + item detail 模式
- 迁移文本节点编辑和 SSE 生成

### P2

- 迁移图片节点的 prompt mention、style reference、上传和生成回写

### P3

- 迁移视频节点的 prompt mention、generation config、task 查询和上传兜底

## 风险

### 风险 1：现有未完成 canvas 代码与新迁移冲突

当前 `aicon` 仓库已有一批未提交的 canvas 改动。迁移时必须以“在现有未完成实现上收敛”为原则，避免回退用户已有工作。

### 风险 2：文本生成从轮询切到 SSE

当前前端 canvas 文本链路没有完整 SSE 消费模型。迁移时要优先打通事件订阅和节点回写，否则文本体验会继续停留在简化版。

### 风险 3：图片/视频 prompt 协议不完整

如果只迁 UI 不迁 `prompt_tokens + resolved_mentions`，生成结果会与旧项目预期明显不一致，尤其是图片引用、文本引用和风格参考。

## 验收标准

- 用户可以在独立画布中创建、编辑并生成文本、图片、视频节点
- 舞台加载不再依赖整图 graph 保存作为主链路
- 文本节点支持流式回写
- 图片和视频节点支持结构化 prompt 输入和结果回写
- 不依赖计费逻辑即可在本地部署中完整运行
