# 部署说明

## 环境要求

- Ubuntu 22.04 LTS 或更高版本
- Docker
- Docker Compose
- 可用公网域名
- HTTPS 证书

## 启动顺序

1. 配置环境变量。
2. 启动 `db` 和 `redis`。
3. 启动 `backend`。
4. 启动 `worker` 和 `beat`。
5. 启动 `frontend`。

## 生产入口

- 前端入口：`https://<domain>/`
- 后端接口：`https://<domain>/api/v1/`
- 接口文档：`https://<domain>/api/docs/`
- 报表文件：`https://<domain>/media/reports/`

## 生产建议

- 生产环境优先使用 [docker-compose.prod.yml](/Users/shizhe/Downloads/demo/docker-compose.prod.yml)。
- 外部仅开放 `80/443`，数据库、Redis、后端 API 只在容器网络内访问。
- 使用 [.env.production.example](/Users/shizhe/Downloads/demo/.env.production.example) 生成 `.env.production`，不要直接复用开发环境的 `.env`。
- 前端容器统一代理 `/api/`、`/admin/`、`/static/` 和 `/media/`。
- 数据库结构请以 Django migrations 为准，`schema.sql` 仅作参考。

## 备份

- PostgreSQL 每日备份。
- 对象存储定期快照。
- Redis 仅作为缓存和队列，不作为唯一数据源。
