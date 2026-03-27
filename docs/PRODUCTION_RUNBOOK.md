# 云服务器上线流程

## 1. 服务器准备

1. 选择 Ubuntu 22.04 LTS 或更高版本的云服务器。
2. 放行 `80`、`443` 端口，关闭不必要的公网端口。
3. 安装 Docker 和 Docker Compose。

## 2. 拉取代码

```bash
git clone <your-repo-url>
cd demo
```

如果是手工上传到服务器，确保目录结构包含：

- `backend/`
- `frontend/`
- `docker-compose.yml`
- `docker-compose.prod.yml`
- `schema.sql`（仅参考，不参与自动初始化）

## 3. 配置环境变量

复制模板并修改：

```bash
cp .env.production.example .env.production
```

建议至少填写：

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=false`
- `DJANGO_ALLOWED_HOSTS=your.domain.com`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://your.domain.com`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `REDIS_URL`
- `CORS_ALLOWED_ORIGINS=https://your.domain.com`
- 外部 API Key

## 4. 首次启动

```bash
make prod-recreate
```

首次启动时会自动：

- 拉起 PostgreSQL、Redis
- 初始化数据库
- 收集 Django 静态资源
- 启动后端、前端、Celery worker、Celery beat

建议在首次上线前先执行项目测试：

```bash
make test
```

## 5. 数据迁移与管理员初始化

如果首次启动后数据库还未创建完成，可手工执行：

```bash
make prod-migrate
make prod-superuser
```

## 6. 验收检查

1. 打开 `https://your.domain.com/`
2. 登录系统。
3. 完成个人资料。
4. 查看首页推荐。
5. 创建菜谱或饮食记录。
6. 生成周报并下载 PDF。
7. 发布社区帖子并评论。
8. 访问 `https://your.domain.com/api/docs/` 检查接口文档。
9. 访问 `https://your.domain.com/admin/` 检查后台和静态资源是否正常。

## 7. 日常运维

查看日志：

```bash
make prod-logs svc=backend
make prod-logs svc=frontend
make prod-logs svc=worker
make prod-logs svc=beat
```

停止服务：

```bash
make docker-down-prod
```

重启服务：

```bash
make prod-up
```

## 8. 备份恢复

备份数据库：

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml exec db pg_dump -U nutrition_app nutrition_app > backup.sql
```

恢复数据库：

```bash
cat backup.sql | docker compose --env-file .env.production -f docker-compose.prod.yml exec -T db psql -U nutrition_app -d nutrition_app
```

## 9. 更新上线

1. 拉取最新代码。
2. 重新构建镜像。
3. 执行迁移。
4. 重新启动容器。

```bash
git pull
make prod-recreate
make prod-migrate
```

如果项目目录对应的 Compose 项目名不是默认的 `demo`，可显式覆盖：

```bash
make PROJECT=demo-git prod-ps
make PROJECT=demo-git prod-recreate
```

## 10. 常见问题

- 如果前端刷新出现 404，检查 Nginx 的 SPA 回退配置。
- 如果 Swagger 或 Django Admin 样式缺失，检查 `collectstatic` 是否完成，以及 `/static/` 卷映射是否正常。
- 如果报表无法下载，检查 `media/` 卷和 `/media/` 静态映射。
- 如果第三方 API 失败，系统会自动降级，不影响本地核心功能。
- 如果需要 HTTPS，建议在云服务器入口层或 CDN/WAF/负载均衡处终止 TLS，并把 `X-Forwarded-Proto` 传递给应用。
