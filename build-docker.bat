@echo off
REM ==========================================
REM AICG平台 - Docker镜像构建脚本 (Windows)
REM ==========================================

setlocal enabledelayedexpansion

REM 配置
set IMAGE_REGISTRY=aicg
if not "%IMAGE_REGISTRY%"=="" set IMAGE_REGISTRY=%IMAGE_REGISTRY%
set VERSION=latest
if not "%VERSION%"=="" set VERSION=%VERSION%
set BACKEND_IMAGE=%IMAGE_REGISTRY%/aicg-backend:%VERSION%
set FRONTEND_IMAGE=%IMAGE_REGISTRY%/aicg-frontend:%VERSION%

echo ========================================
echo AICG平台 - Docker镜像构建
echo ========================================
echo.

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker未安装，请先安装Docker
    exit /b 1
)

echo ✅ Docker已安装
echo.

REM 构建后端镜像
echo 📦 构建后端镜像...
echo 镜像名称: %BACKEND_IMAGE%
cd backend
docker build -t "%BACKEND_IMAGE%" .
if errorlevel 1 (
    echo ❌ 后端镜像构建失败
    cd ..
    exit /b 1
)
echo ✅ 后端镜像构建成功
cd ..
echo.

REM 构建前端镜像
echo 📦 构建前端镜像...
echo 镜像名称: %FRONTEND_IMAGE%
cd frontend
docker build -t "%FRONTEND_IMAGE%" .
if errorlevel 1 (
    echo ❌ 前端镜像构建失败
    cd ..
    exit /b 1
)
echo ✅ 前端镜像构建成功
cd ..
echo.

REM 显示镜像信息
echo ========================================
echo 🎉 所有镜像构建完成！
echo ========================================
echo.
echo 构建的镜像:
docker images | findstr "%IMAGE_REGISTRY%/aicg"
echo.

REM 提示下一步操作
echo ========================================
echo 下一步操作:
echo ========================================
echo.
echo 1. 测试镜像:
echo    docker-compose -f docker-compose.prod.yml up -d
echo.
echo 2. 推送到镜像仓库:
echo    docker push %BACKEND_IMAGE%
echo    docker push %FRONTEND_IMAGE%
echo.
echo 3. 标记为其他版本:
echo    docker tag %BACKEND_IMAGE% %IMAGE_REGISTRY%/aicg-backend:v1.0.0
echo    docker tag %FRONTEND_IMAGE% %IMAGE_REGISTRY%/aicg-frontend:v1.0.0
echo.

endlocal
