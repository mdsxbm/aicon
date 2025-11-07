# Implementation Plan: AICG内容分发平台

**Branch**: `001-aicg-platform` | **Date**: 2025-11-06 | **Spec**: [AICG内容分发平台规格说明书](spec.md)
**Input**: Feature specification from `/specs/001-aicg-platform/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

AICG内容分发平台是一个AI驱动的长文本到视频自动转换系统，支持超长文本（百万字级别）的分章节处理、异步视频生成和多平台分发。核心技术架构采用分层设计：展示层（Web UI）、应用层（业务逻辑）、集成层（AI服务调用）、基础设施层（存储和队列），确保系统可扩展性和高可用性。关键特性包括智能章节识别、渐进式内容处理、异步任务队列、实时进度跟踪、用户控制的API密钥管理和分层存储策略。

## Technical Context

**Language/Version**: Python 3.11+ (后端), Vue.js 3+ (前端)
**Primary Dependencies**: FastAPI, Celery, Redis, PostgreSQL, MinIO, FFmpeg, SQLAlchemy, Alembic
**Package Management**: uv (后端Python包管理), npm/pnpm (前端)
**Storage**: PostgreSQL (关系数据), Redis (缓存/队列), MinIO (对象存储)
**Testing**: pytest (后端), Vitest + Vue Test Utils (前端)
**Logging**: structlog (结构化日志), loguru (统一日志管理)
**Error Handling**: 自定义异常体系，统一错误响应中间件
**Target Platform**: Linux服务器 (后端), 现代浏览器 (前端)
**Project Type**: web (前后端分离架构)
**Performance Goals**: 100+并发生成任务, 百万字文档30秒内章节切割, 99.9%系统可用性
**Constraints**: 图像生成30-60秒/张(第三方API), 视频文件2GB上限, API调用频率限制
**Scale/Scope**: 单用户模式, 支持百万字级文本文件, 100+并发生成任务, 分层存储策略

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### 必须验证的宪法原则

- **用户价值优先**: ✅ 技术架构聚焦于文本到视频转换的核心需求，消除技术障碍
- **渐进式处理**: ✅ 分阶段处理流程设计（上传→切割→解析→确认→生成）
- **异步优先架构**: ✅ 使用Celery异步队列处理AI密集型操作
- **分层系统设计**: ✅ 前后端分离，清晰的四层架构设计
- **全面可观测性**: ✅ 集成结构化日志和监控体系

### 性能标准验证

- ✅ 百万字文档章节切割：30秒内（符合宪法要求）
- ✅ 图像生成：30-60秒/张（考虑第三方API现实约束）
- ✅ 系统设计支持99.9%可用性
- ✅ 核心页面加载目标3秒内

### 代码质量验证

- ✅ 所有功能设计为独立可测试
- ✅ 外部AI服务集成包含合同测试计划
- ✅ 端到端用户工作流有集成测试设计
- ✅ 包含静态分析和安全扫描计划

**宪法检查状态**: ✅ 通过 - 无违规项，所有设计符合宪法原则

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Web application structure
backend/
├── pyproject.toml       # uv项目配置文件
├── src/
│   ├── models/          # SQLAlchemy models and database schemas
│   │   ├── __init__.py
│   │   ├── base.py       # 基础模型类
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── chapter.py
│   │   ├── paragraph.py
│   │   ├── sentence.py   # 句子模型 - 最小视频生成单元
│   │   ├── generation_task.py
│   │   ├── publication_record.py
│   │   └── api_config.py
│   ├── services/        # Business logic services
│   │   ├── __init__.py
│   │   ├── text_parser.py      # 文本解析服务
│   │   ├── chapter_service.py   # 章节管理服务
│   │   ├── sentence_service.py  # 句子处理服务
│   │   ├── video_generator.py   # 视频生成服务
│   │   ├── timeline_service.py  # 时间轴处理服务
│   │   ├── subtitle_service.py  # 字幕生成服务
│   │   ├── video_synthesis.py   # 视频合成服务 (ffmpeg-python)
│   │   ├── publisher.py         # 发布服务
│   │   └── api_manager.py       # API密钥管理服务
│   ├── api/             # FastAPI routes and endpoints
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── projects.py
│   │   │   ├── chapters.py
│   │   │   ├── paragraphs.py     # 段落API
│   │   │   ├── sentences.py      # 句子API
│   │   │   ├── generation.py
│   │   │   └── publications.py
│   │   ├── dependencies.py
│   │   └── middleware.py         # 中间件（异常处理、日志等）
│   ├── core/            # Core application components
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── database.py
│   │   ├── logging.py           # 统一日志配置
│   │   └── exceptions.py        # 自定义异常类
│   ├── workers/         # Celery task definitions
│   │   ├── __init__.py
│   │   ├── base.py            # 基础任务类
│   │   ├── text_processing.py  # 文本处理任务
│   │   ├── sentence_tasks.py   # 句子级别处理任务
│   │   ├── image_generation.py # 图片生成任务
│   │   ├── audio_generation.py # 音频生成任务
│   │   ├── timeline_tasks.py   # 时间轴处理任务
│   │   ├── subtitle_tasks.py   # 字幕处理任务
│   │   ├── video_synthesis.py  # 视频合成任务 (ffmpeg-python)
│   │   └── publication_tasks.py # 发布任务
│   ├── utils/           # Utility functions
│   │   ├── __init__.py
│   │   ├── file_handlers.py
│   │   ├── validators.py
│   │   ├── time_utils.py       # 时间处理工具
│   │   ├── text_utils.py       # 文本处理工具
│   │   ├── ffmpeg_utils.py     # FFmpeg工具函数
│   │   └── subtitle_utils.py   # 字幕工具函数
│   └── main.py          # FastAPI应用入口
├── tests/
│   ├── __init__.py
│   ├── conftest.py       # pytest配置
│   ├── unit/            # Unit tests
│   │   ├── test_models/
│   │   ├── test_services/
│   │   └── test_utils/
│   ├── integration/     # Integration tests
│   │   ├── test_api/
│   │   └── test_workers/
│   └── contract/        # Contract tests for external APIs
├── migrations/          # Alembic database migrations
├── scripts/             # 部署和维护脚本
├── Dockerfile
└── README.md

frontend/
├── package.json
├── vite.config.js
├── src/
│   ├── components/      # Vue.js components
│   │   ├── common/       # Reusable components
│   │   ├── project/      # Project management components
│   │   ├── chapter/      # Chapter editing components
│   │   ├── sentence/      # 句子编辑组件
│   │   ├── paragraph/    # 段落管理组件
│   │   ├── generation/   # Video generation components
│   │   ├── timeline/     # 时间轴组件
│   │   ├── subtitle/     # 字幕管理组件
│   │   └── publication/  # Publishing components
│   ├── views/           # Page-level components
│   │   ├── Dashboard.vue
│   │   ├── ProjectDetail.vue
│   │   ├── ChapterEditor.vue
│   │   ├── SentenceEditor.vue  # 句子编辑页面
│   │   ├── TimelineEditor.vue  # 时间轴编辑页面
│   │   ├── SubtitleEditor.vue  # 字幕编辑页面
│   │   ├── GenerationQueue.vue
│   │   └── Settings.vue
│   ├── services/        # API service layer
│   │   ├── api.js
│   │   ├── auth.js
│   │   ├── projects.js
│   │   ├── chapters.js
│   │   ├── sentences.js  # 句子相关API服务
│   │   ├── timeline.js    # 时间轴API服务
│   │   ├── subtitles.js   # 字幕API服务
│   │   └── generations.js
│   ├── stores/          # Pinia state management
│   │   ├── auth.js
│   │   ├── projects.js
│   │   ├── chapters.js
│   │   ├── sentences.js  # 句子状态管理
│   │   ├── timeline.js    # 时间轴状态管理
│   │   ├── subtitles.js   # 字幕状态管理
│   │   └── generations.js
│   ├── router/          # Vue Router configuration
│   ├── utils/           # Utility functions
│   └── assets/          # Static assets
├── tests/               # Vitest tests
└── README.md
```

**Structure Decision**: 采用前后端分离的Web应用架构，后端使用uv管理Python依赖，包含完整的数据层次模型（用户→项目→章节→段落→句子），统一的日志管理系统（structlog + loguru）和异常处理机制，确保句子作为最小视频生成单元的完整支持

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
