# 上线验证报告

## 验证范围

本次验证围绕两类目标展开：

- 生产部署加固是否已经具备基础上线条件
- 当前代码是否通过关键运行级检查和核心用户链路烟雾测试

## 已完成的生产化改造

- 新增生产编排文件 [docker-compose.prod.yml](/Users/shizhe/Downloads/demo/docker-compose.prod.yml)
- 新增生产环境模板 [.env.production.example](/Users/shizhe/Downloads/demo/.env.production.example)
- 新增后端生产启动脚本 [backend/entrypoint.prod.sh](/Users/shizhe/Downloads/demo/backend/entrypoint.prod.sh)
- 收紧 Django 默认安全配置 [backend/config/settings.py](/Users/shizhe/Downloads/demo/backend/config/settings.py)
- 补齐前端 Nginx 对 `/api/`、`/admin/`、`/static/`、`/media/` 的代理与映射 [frontend/nginx.conf](/Users/shizhe/Downloads/demo/frontend/nginx.conf)
- 区分开发环境和生产环境部署说明 [docs/PRODUCTION_RUNBOOK.md](/Users/shizhe/Downloads/demo/docs/PRODUCTION_RUNBOOK.md)
- 升级后端数据库驱动依赖以兼容 Python 3.14 [backend/requirements.txt](/Users/shizhe/Downloads/demo/backend/requirements.txt)

## 实际执行的检查

### 1. 代码语法检查

执行命令：

```bash
python3 -m py_compile $(rg --files backend -g '*.py')
```

结果：

- 通过

### 2. 前端依赖安装与生产构建

执行命令：

```bash
npm install
npm run build
```

结果：

- 通过
- 已成功生成前端生产构建产物

补充观察：

- 主 JS chunk 体积超过 500 kB，当前仍有体积优化空间

### 3. Django 运行检查

执行命令：

```bash
../.venv/bin/python manage.py check
```

结果：

- 通过

### 4. Django 部署检查

执行命令：

```bash
DJANGO_SECRET_KEY=<强随机值> \
DJANGO_DEBUG=false \
DJANGO_ALLOWED_HOSTS=example.com \
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com \
CORS_ALLOW_ALL_ORIGINS=false \
CORS_ALLOWED_ORIGINS=https://example.com \
DJANGO_SECURE_SSL_REDIRECT=true \
../.venv/bin/python manage.py check --deploy
```

结果：

- 通过
- 当前剩余项主要是 `drf-spectacular` 的 schema 注解警告，不影响核心业务运行和部署检查通过

### 4.1 OpenAPI schema 生成

执行命令：

```bash
DJANGO_SECRET_KEY=<强随机值> \
DJANGO_DEBUG=false \
DJANGO_ALLOWED_HOSTS=example.com \
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com \
CORS_ALLOW_ALL_ORIGINS=false \
CORS_ALLOWED_ORIGINS=https://example.com \
DJANGO_SECURE_SSL_REDIRECT=true \
../.venv/bin/python manage.py spectacular --file backend/openapi.yaml
```

结果：

- 通过
- 已生成 [backend/openapi.yaml](/Users/shizhe/Downloads/demo/backend/openapi.yaml)

### 5. 后端核心烟雾测试

执行命令：

```bash
../.venv/bin/python manage.py test apps.common.tests
```

结果：

- 通过
- 共 5 条主链路测试全部通过

覆盖链路：

- 注册、登录、资料维护、营养分析
- 菜谱推荐、推荐解释、收藏
- 饮食记录、统计、报表生成
- 健康目标与进度记录
- 社区发帖、评论、举报
- 外部 API 降级返回

## 用户视角验收结论

结合前端构建成功和后端烟雾测试结果，当前系统核心用户路径可判断为：

- 新用户注册并登录：通过
- 完善个人资料并生成健康分析：通过
- 查看首页推荐和推荐理由：通过
- 录入饮食记录并查看统计：通过
- 创建健康目标并追加进度：通过
- 社区发帖、评论、举报：通过
- 生成并下载阶段性报表：通过后端生成链路

## 当前剩余风险

### 1. 当前环境无法完成 Docker 容器联调

原因：

- 当前执行环境中不存在 `docker` 命令，因此无法在本机直接完成 `docker compose up --build` 验证

影响：

- 代码和部署文件已准备好，但容器级联调仍需要在具备 Docker 的机器或云服务器上执行一次

### 2. API 文档 schema 仍存在注解不足

当前状态：

- 已完成主要 API 的 schema 注解补充
- OpenAPI 文件可以正常生成

剩余说明：

- 当前运行环境仍会输出 `requests` 依赖兼容性 warning
- 不影响业务接口使用，也不阻塞 OpenAPI 文件生成

### 3. 前端构建体积偏大

表现：

- 构建输出提示部分 chunk 超过默认警戒值

影响：

- 首屏加载性能仍有优化空间

## 是否可以上线

结论分两层：

- 作为答辩演示版、内测版、封闭环境部署版：可以上线
- 作为正式公网生产版：基本具备条件，但建议在云服务器上补做一次 Docker 联调和域名/HTTPS 实机验证后再放量

## 上云前最后一轮建议

1. 在目标云服务器执行生产编排启动：

```bash
cp .env.production.example .env.production
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

2. 完成以下人工验收：

- 打开首页并登录
- 查看 `/api/docs/` 是否正常
- 查看 `/admin/` 样式是否正常
- 测试报表下载链接
- 检查 `backend`、`frontend`、`worker`、`beat` 日志

3. 如果计划正式公网开放，再补一轮：

- HTTPS 证书接入
- 域名回源验证
- 数据库备份验证
- 日志告警接入
