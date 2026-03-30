# 国内网络优化部署指南

## 问题
在国内服务器上执行 `docker compose build` 时，由于网络原因经常卡住或下载速度极慢。

## 解决方案

### 方案 1: 本地构建 + 上传（推荐）⭐

在本地（你的电脑）构建前端，然后只上传构建好的文件到服务器，避免在服务器上进行耗时的 npm 安装。

#### 使用 Makefile（最简单）
```bash
# 一键本地构建并部署到服务器
make deploy-frontend-dist

# 或者只构建不上传
make build-frontend-local
```

#### 使用脚本
```bash
# 使用本地构建脚本
./scripts/build-frontend-local.sh

# 脚本会自动:
# 1. 在本地安装依赖
# 2. 构建生产版本
# 3. 上传到服务器
# 4. 在服务器上部署
```

#### 手动操作
```bash
# 1. 本地构建
cd frontend
npm install
npm run build

# 2. 上传到服务器
scp -r dist root@121.41.102.152:/tmp/frontend-dist

# 3. 在服务器上部署
ssh root@121.41.102.152
cd /root/demo-git
docker compose -p demo --env-file .env.production -f docker-compose.prod.yml stop frontend
mkdir -p frontend/dist
rm -rf frontend/dist/*
cp -r /tmp/frontend-dist/dist/* frontend/dist/
docker compose -p demo --env-file .env.production -f docker-compose.prod.yml start frontend
```

### 方案 2: 优化服务器 Docker 配置

在服务器上配置 Docker 镜像加速器：

```bash
# 1. 在服务器上创建 Docker 配置
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://docker.1panel.live",
    "https://dockerhub.icu",
    "https://docker.chenby.cn",
    "https://docker.awsl9527.cn"
  ],
  "max-concurrent-downloads": 10,
  "max-download-attempts": 5
}
EOF

# 2. 重启 Docker
sudo systemctl daemon-reload
sudo systemctl restart docker

# 3. 验证配置
docker info | grep -A 10 "Registry Mirrors"
```

### 方案 3: 使用服务器部署脚本

项目提供了优化后的服务器部署脚本：

```bash
# 上传脚本到服务器
scp scripts/deploy-server.sh root@121.41.102.152:/root/demo-git/

# 在服务器上执行
ssh root@121.41.102.152
cd /root/demo-git
chmod +x scripts/deploy-server.sh
./scripts/deploy-server.sh
```

## 推荐工作流程

### 日常开发（前端修改）
```bash
# 本地修改代码
# 快速部署到服务器
make deploy-frontend-dist
```

### 日常开发（后端修改）
```bash
# 只需重启后端容器，无需重新构建
ssh root@121.41.102.152
cd /root/demo-git
docker compose -p demo --env-file .env.production -f docker-compose.prod.yml restart backend worker
```

### 完整部署（大版本更新）
```bash
# 1. 本地构建前端
make build-frontend-local

# 2. 上传到服务器
scp -r frontend/dist root@121.41.102.152:/tmp/

# 3. 在服务器上拉取代码并部署
ssh root@121.41.102.152
cd /root/demo-git
git pull origin main
docker compose -p demo --env-file .env.production -f docker-compose.prod.yml up -d --build backend worker
# 然后手动复制前端文件到 nginx 容器
```

## 优化说明

项目已做以下优化：
- ✅ Dockerfile 配置了淘宝 npm 镜像源
- ✅ 添加了 .npmrc 配置文件
- ✅ 使用了 Docker BuildKit
- ✅ 优化了 npm 缓存策略
- ✅ 提供了本地构建脚本

## 故障排查

### 构建仍然很慢
1. 检查是否使用了镜像加速器：`docker info | grep Registry`
2. 尝试使用方案 1（本地构建）
3. 检查服务器网络连接

### npm install 失败
```bash
# 清理缓存重试
npm cache clean --force
npm install
```

### 权限问题
```bash
# 确保脚本有执行权限
chmod +x scripts/*.sh
```

## 对比

| 方案 | 速度 | 复杂度 | 推荐场景 |
|------|------|--------|----------|
| 本地构建+上传 | ⚡️ 最快 | 简单 | 前端频繁修改 |
| 服务器优化构建 | 🚀 快 | 中等 | 后端修改 |
| 直接构建 | 🐢 慢 | 最简单 | 偶尔部署 |
