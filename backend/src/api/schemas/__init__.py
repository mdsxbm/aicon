"""
API Schemas模块 - 集中导出所有Pydantic模型
"""

# 认证相关
from .auth import (
    MessageResponse,
    TokenResponse,
    TokenVerifyResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)

# 用户相关
from .user import (
    AvatarDeleteResponse,
    AvatarInfoResponse,
    AvatarUploadResponse,
    PasswordChangeRequest,
    PasswordChangeResponse,
    UserDeleteRequest,
    UserResponse,
    UserStatsResponse,
    UserUpdateRequest,
)

# 项目相关
from .project import (
    ProjectArchiveResponse,
    ProjectCreate,
    ProjectDeleteResponse,
    ProjectListResponse,
    ProjectProcessingResponse,
    ProjectResponse,
    ProjectRetryResponse,
    ProjectStatusResponse,
    ProjectUpdate,
)

# 章节相关
from .chapter import (
    ChapterConfirmResponse,
    ChapterCreate,
    ChapterDeleteResponse,
    ChapterListResponse,
    ChapterResponse,
    ChapterStatusResponse,
    ChapterUpdate,
)

# 段落相关
from .paragraph import (
    ParagraphBatchUpdate,
    ParagraphBatchUpdateItem,
    ParagraphCreate,
    ParagraphDeleteResponse,
    ParagraphListResponse,
    ParagraphResponse,
    ParagraphUpdate,
)

# 句子相关
from .sentence import (
    SentenceCreate,
    SentenceListResponse,
    SentenceResponse,
    SentenceUpdate,
)

# 文件相关
from .file import (
    FileBatchDeleteResponse,
    FileCleanupResponse,
    FileDeleteResponse,
    FileInfo,
    FileIntegrityCheckResponse,
    FileIntegrityCheckResult,
    FileListResponse,
    FileResponse,
    FileStorageUsageResponse,
    FileType,
    FileUploadResponse,
    FileUploadResult,
)

# API密钥相关
from .api_key import (
    APIKeyCreate,
    APIKeyDeleteResponse,
    APIKeyListResponse,
    APIKeyResponse,
    APIKeyUpdate,
    APIKeyUsageResponse,
)

# 任务相关
from .task import TaskStatusResponse

# 提示词相关
from .prompt import (
    PromptGenerateByIdsRequest,
    PromptGenerateRequest,
    PromptGenerateResponse,
)

# 图片相关
from .image import (
    ImageGenerateRequest,
    ImageGenerateResponse,
)

# 音频相关
from .audio import (
    AudioGenerateRequest,
    AudioGenerateResponse,
)

# 视频任务相关
from .video_task import (
    VideoTaskCreate,
    VideoTaskDeleteResponse,
    VideoTaskListResponse,
    VideoTaskResponse,
    VideoTaskRetryResponse,
    VideoTaskStatsResponse,
)

__all__ = [
    # 认证
    "UserLogin",
    "UserRegister",
    "TokenResponse",
    "TokenVerifyResponse",
    "MessageResponse",
    "UserResponse",
    # 用户
    "UserUpdateRequest",
    "PasswordChangeRequest",
    "UserStatsResponse",
    "UserDeleteRequest",
    "PasswordChangeResponse",
    "AvatarUploadResponse",
    "AvatarDeleteResponse",
    "AvatarInfoResponse",
    # 项目
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectListResponse",
    "ProjectDeleteResponse",
    "ProjectArchiveResponse",
    "ProjectProcessingResponse",
    "ProjectRetryResponse",
    "ProjectStatusResponse",
    # 章节
    "ChapterCreate",
    "ChapterUpdate",
    "ChapterResponse",
    "ChapterListResponse",
    "ChapterDeleteResponse",
    "ChapterConfirmResponse",
    "ChapterStatusResponse",
    # 段落
    "ParagraphCreate",
    "ParagraphUpdate",
    "ParagraphResponse",
    "ParagraphBatchUpdateItem",
    "ParagraphBatchUpdate",
    "ParagraphListResponse",
    "ParagraphDeleteResponse",
    # 句子
    "SentenceCreate",
    "SentenceUpdate",
    "SentenceResponse",
    "SentenceListResponse",
    # 文件
    "FileUploadResponse",
    "FileUploadResult",
    "FileInfo",
    "FileResponse",
    "FileListResponse",
    "FileDeleteResponse",
    "FileCleanupResponse",
    "FileStorageUsageResponse",
    "FileBatchDeleteResponse",
    "FileIntegrityCheckResult",
    "FileIntegrityCheckResponse",
    "FileType",
    # API密钥
    "APIKeyCreate",
    "APIKeyUpdate",
    "APIKeyResponse",
    "APIKeyListResponse",
    "APIKeyDeleteResponse",
    "APIKeyUsageResponse",
    # 任务
    "TaskStatusResponse",
    # 提示词
    "PromptGenerateRequest",
    "PromptGenerateResponse",
    "PromptGenerateByIdsRequest",
    # 图片
    "ImageGenerateRequest",
    "ImageGenerateResponse",
    # 音频
    "AudioGenerateRequest",
    "AudioGenerateResponse",
    # 视频任务
    "VideoTaskCreate",
    "VideoTaskResponse",
    "VideoTaskListResponse",
    "VideoTaskStatsResponse",
    "VideoTaskDeleteResponse",
    "VideoTaskRetryResponse",
]