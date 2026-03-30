#!/bin/bash

# 服务器端快速部署脚本
# 使用 Docker BuildKit 和缓存优化构建速度

set -e

PROJECT_NAME="demo"
ENV_FILE=".env.production"
COMPOSE_FILE="docker-compose.prod.yml"

echo "🚀 开始部署..."

# 检查是否在正确的目录
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ 错误: 请在项目根目录执行此脚本"
    exit 1
fi

# 拉取最新代码
echo "📥 拉取最新代码..."
git pull origin main

# 使用 BuildKit 和缓存优化构建
echo "🔨 构建并启动服务..."
DOCKER_BUILDKIT=1 docker compose \
    -p $PROJECT_NAME \
    --env-file $ENV_FILE \
    -f $COMPOSE_FILE \
    up \
    -d \
    --build \
    --force-recreate \
    frontend

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 显示服务状态
echo "📊 服务状态:"
docker compose \
    -p $PROJECT_NAME \
    --env-file $ENV_FILE \
    -f $COMPOSE_FILE \
    ps

echo "✅ 部署完成!"
echo "💡 查看日志: docker compose -p demo --env-file $ENV_FILE -f $COMPOSE_FILE logs -f frontend"
