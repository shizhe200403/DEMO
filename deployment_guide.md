# 云服务器部署方案

## 1. 部署目标

- 支持毕业设计演示。
- 支持后续低成本上线到云服务器。
- 支持横向扩展和基础监控。
- 尽量避免复杂但不必要的云原生组件。

## 2. 推荐部署架构

- `Nginx`：反向代理、静态资源托管、HTTPS、压缩、缓存控制。
- `Gunicorn`：承载 Django WSGI 应用。
- `Django REST Framework`：后端 API。
- `Celery`：异步任务执行。
- `Redis`：缓存、任务队列。
- `PostgreSQL`：主业务数据库。
- `MinIO`：图片、附件、PDF 存储。
- `Vue 3 + Vite`：前端静态资源构建后由 Nginx 托管。

## 3. 容器化建议

建议将系统拆成以下容器：

- `frontend`
- `backend`
- `worker`
- `scheduler`
- `postgres`
- `redis`
- `minio`
- `nginx`

其中：

- `backend` 只负责 Web API。
- `worker` 处理推荐预计算、PDF 生成、图片压缩、定时任务。
- `scheduler` 负责定时调度。

## 4. 环境变量

建议至少配置以下环境变量：

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET_KEY`
- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `EXTERNAL_USDA_API_KEY`
- `EXTERNAL_NUTRITIONIX_APP_ID`
- `EXTERNAL_NUTRITIONIX_API_KEY`
- `EXTERNAL_EDAMAM_APP_ID`
- `EXTERNAL_EDAMAM_APP_KEY`

## 5. 部署步骤

### 5.1 前端

1. 执行生产构建。
2. 将静态文件部署到 Nginx 指定目录。
3. 配置前端路由回退，避免刷新 404。

### 5.2 后端

1. 安装依赖或使用镜像。
2. 执行数据库迁移。
3. 收集静态文件。
4. 启动 Gunicorn。
5. 将 API 通过 Nginx 暴露。

### 5.3 异步任务

1. 启动 Redis。
2. 启动 Celery worker。
3. 启动 Celery beat。
4. 验证任务队列、周期任务和失败重试。

### 5.4 数据库与对象存储

1. PostgreSQL 需要配置定期备份。
2. MinIO 或对象存储需要配置生命周期和访问权限。
3. 关键文件建议保留副本或快照。

## 6. Nginx 关键点

- 配置 API 反向代理到后端服务。
- 配置静态文件和上传文件访问路径。
- 开启 HTTPS 和 HTTP 自动跳转。
- 设置合适的缓存头和 gzip 压缩。

## 7. 安全建议

- 生产环境关闭 `DEBUG`。
- 密钥不写入前端代码仓库。
- 接口启用限流和权限控制。
- 登录、重置密码、敏感操作做验证码或二次确认。
- 上传文件要校验类型、大小和路径，防止恶意文件。

## 8. 备份与恢复

- 数据库每日自动备份。
- 对象存储按天或按周快照。
- 保留最近多个版本的备份。
- 定期演练恢复流程。

## 9. 监控与日志

- 后端日志需要区分业务日志、错误日志和审计日志。
- 任务队列需要记录成功、失败和重试情况。
- 至少保留接口错误、慢查询、登录异常、任务失败等可观测信息。

## 10. 上线检查清单

- 数据库迁移已完成。
- 管理员账号已初始化。
- 外部 API Key 已配置。
- HTTPS 证书已部署。
- 文件上传目录可用。
- 前端页面刷新正常。
- 报表导出可用。
- 异步任务可执行。
- 日志和备份策略已验证。
