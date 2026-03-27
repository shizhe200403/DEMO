# 云服务器部署命令清单

## 1. 首次准备

适用环境：

- Ubuntu 22.04+
- 已有公网 IP
- 已解析域名到服务器

更新系统：

```bash
sudo apt update && sudo apt upgrade -y
```

安装基础工具：

```bash
sudo apt install -y ca-certificates curl gnupg lsb-release git
```

安装 Docker：

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

说明：

- 执行完 `usermod` 后重新登录一次服务器，再继续下面步骤
- 如果服务器已经预装 Docker，可以先执行 `docker --version` 和 `docker compose version`，确认可用后跳过安装

## 1.1 先给 2G 内存服务器加 Swap

推荐创建 2G Swap，避免 Docker 构建时被 OOM：

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h
```

## 2. 获取项目

克隆仓库：

```bash
git clone <your-repo-url>
cd demo
```

如果是本地上传：

```bash
scp -r ./demo <user>@<server-ip>:/home/<user>/
ssh <user>@<server-ip>
cd /home/<user>/demo
```

## 3. 配置生产环境变量

复制模板：

```bash
cp .env.production.example .env.production
```

编辑配置：

```bash
vim .env.production
```

至少修改以下内容：

```env
DJANGO_SECRET_KEY=替换成长度足够的随机密钥
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=your.domain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://your.domain.com
DB_PASSWORD=替换成强密码
CORS_ALLOWED_ORIGINS=https://your.domain.com
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true
DJANGO_SECURE_SSL_REDIRECT=false
```

说明：

- 如果你当前先用公网 IP 上线，而不是域名，请先改成：

```env
DJANGO_ALLOWED_HOSTS=<你的公网IP>
DJANGO_CSRF_TRUSTED_ORIGINS=http://<你的公网IP>
CORS_ALLOWED_ORIGINS=http://<你的公网IP>
SESSION_COOKIE_SECURE=false
CSRF_COOKIE_SECURE=false
DJANGO_SECURE_SSL_REDIRECT=false
GUNICORN_WORKERS=2
CELERY_WORKER_CONCURRENCY=1
```

- 如果 HTTPS 在云厂商负载均衡或 CDN 层终止，先保留 `DJANGO_SECURE_SSL_REDIRECT=false`
- 确认代理层把 `X-Forwarded-Proto=https` 传给应用后，再改成 `true`

## 4. 启动生产环境

构建并启动：

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

查看容器状态：

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

查看日志：

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f backend
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f frontend
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f worker
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f beat
```

## 5. 初始化管理员

创建超级管理员：

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

## 6. 上线后检查

健康检查：

```bash
curl http://127.0.0.1/healthz
```

页面检查：

```bash
curl -I http://127.0.0.1/
curl -I http://127.0.0.1/api/v1/health/
curl -I http://127.0.0.1/api/docs/
curl -I http://127.0.0.1/admin/
```

手工浏览器检查：

1. 打开首页
2. 登录系统
3. 完善个人资料
4. 新增饮食记录
5. 生成周报
6. 发布一条社区帖子

## 7. 更新发布

拉取新代码并重建：

```bash
git pull
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

如果有迁移：

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml exec backend python manage.py migrate
```

## 8. 停止与重启

停止：

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml down
```

重启：

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

## 9. 数据备份

备份 PostgreSQL：

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml exec db pg_dump -U nutrition_app nutrition_app > backup-$(date +%F-%H%M%S).sql
```

恢复 PostgreSQL：

```bash
cat backup.sql | docker compose --env-file .env.production -f docker-compose.prod.yml exec -T db psql -U nutrition_app -d nutrition_app
```

## 10. 推荐放行端口

云服务器安全组：

- `22/tcp`
- `80/tcp`
- `443/tcp`

不要公网开放：

- `5432/tcp`
- `6379/tcp`
- `8000/tcp`

## 11. 当前项目对应的关键文件

- 生产编排：[docker-compose.prod.yml](/Users/shizhe/Downloads/demo/docker-compose.prod.yml)
- 生产环境模板：[.env.production.example](/Users/shizhe/Downloads/demo/.env.production.example)
- 阿里云单机部署说明：[docs/ALIYUN_SINGLE_SERVER_DEPLOYMENT.md](/Users/shizhe/Downloads/demo/docs/ALIYUN_SINGLE_SERVER_DEPLOYMENT.md)
- 上线手册：[docs/PRODUCTION_RUNBOOK.md](/Users/shizhe/Downloads/demo/docs/PRODUCTION_RUNBOOK.md)
- 上线验证报告：[docs/RELEASE_VALIDATION.md](/Users/shizhe/Downloads/demo/docs/RELEASE_VALIDATION.md)
