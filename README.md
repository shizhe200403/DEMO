# 智能菜谱推荐与营养健康管理系统

## 项目目标

本项目面向真实饮食管理场景，提供菜谱推荐、营养分析、饮食记录、健康目标管理、社区互动和云端部署能力。系统采用前后端分离架构，后端以 Django REST Framework 构建，前端以 Vue 3 + Vite + TypeScript 实现。

## 当前能力

- 用户注册、登录、个人资料、健康档案
- 菜谱管理、食材管理、菜谱营养汇总
- 饮食记录、健康目标、进度追踪
- 推荐引擎、营养分析、行为埋点
- 社区发帖、评论、举报、内容治理
- 周报、月报、PDF 导出
- 外部开放平台数据代理
- Docker Compose 一键部署

## 目录结构

- `backend/` Django 后端
- `frontend/` Vue 前端
- `docs/` 项目文档
- `schema.sql` PostgreSQL 结构参考脚本
- `docker-compose.yml` 本地与云端部署编排

## 本地开发

1. 复制环境变量模板。
2. 启动数据库和 Redis。
3. 启动后端与前端。
4. 通过浏览器访问前端页面。

常用命令：

```bash
make check
make test
make docker-up
make docker-down
```

## 云端部署

推荐使用 Docker Compose 部署到 Ubuntu 22.04+ 云服务器。

- 开发环境使用 [docker-compose.yml](/Users/shizhe/Downloads/demo/docker-compose.yml)
- 生产环境使用 [docker-compose.prod.yml](/Users/shizhe/Downloads/demo/docker-compose.prod.yml)
- 生产环境变量模板使用 [.env.production.example](/Users/shizhe/Downloads/demo/.env.production.example)

生产编排默认只对外暴露前端 `80` 端口，Nginx 会统一代理 `/api/`、`/admin/`、`/static/` 和 `/media/`。数据库结构以 Django migrations 为准，`schema.sql` 仅用于参考和手工排查。

推荐直接使用 `Makefile` 中的生产命令入口：

```bash
make prod-build
make prod-recreate
make prod-ps
make prod-health
make prod-logs svc=backend
make prod-migrate
make prod-superuser
```

如果生产环境目录名不是 `demo`，可以覆盖 Compose 项目名：

```bash
make PROJECT=demo-git prod-ps
```

## 参考文档

- [数据库设计](/Users/shizhe/Downloads/demo/database_design.md)
- [接口清单](/Users/shizhe/Downloads/demo/api_spec.md)
- [部署方案](/Users/shizhe/Downloads/demo/deployment_guide.md)
- [论文与答辩材料](/Users/shizhe/Downloads/demo/docs/THESIS_DEFENSE_MATERIALS.md)
- [用户验收与体验优化清单](/Users/shizhe/Downloads/demo/docs/UAT_CHECKLIST_AND_UX_OPTIMIZATION.md)
- [上线验证报告](/Users/shizhe/Downloads/demo/docs/RELEASE_VALIDATION.md)
- [云服务器部署命令清单](/Users/shizhe/Downloads/demo/docs/CLOUD_DEPLOY_COMMANDS.md)
- [阿里云单机部署说明](/Users/shizhe/Downloads/demo/docs/ALIYUN_SINGLE_SERVER_DEPLOYMENT.md)
- [上线手册](/Users/shizhe/Downloads/demo/docs/PRODUCTION_RUNBOOK.md)
- [用户指南](/Users/shizhe/Downloads/demo/docs/USER_GUIDE.md)
