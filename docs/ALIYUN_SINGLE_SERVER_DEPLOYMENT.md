# 阿里云单机部署说明

## 1. 适用服务器

当前说明针对以下配置编写：

- 阿里云 ECS
- Ubuntu 22.04 64 位
- 2 vCPU / 2 GiB 内存
- 40 GiB ESSD Entry
- 3 Mbps 公网带宽
- 单台服务器承载全部服务

## 2. 是否适合当前项目

可以部署当前项目，但定位要明确：

- 适合毕业设计答辩
- 适合个人演示和小范围试用
- 不适合一开始就承载明显并发流量

原因很直接：

- 2 GiB 内存可以跑完整服务栈，但资源比较紧
- Docker 构建镜像时容易吃内存
- PostgreSQL、Redis、Django、Celery、Nginx 同机运行时，必须控制进程并发

## 3. 当前项目在这台机器上的部署方式

全部部署在一台服务器中，服务拆分为多个容器：

- `frontend`：Nginx + 前端静态文件
- `backend`：Django + Gunicorn
- `db`：PostgreSQL
- `redis`：Redis
- `worker`：Celery worker
- `beat`：Celery beat

对外只暴露：

- `80`
- `443`（后续如果接 HTTPS）

内部容器互通：

- 前端访问后端 API
- 后端访问数据库和 Redis
- Celery worker/beat 访问 Redis 和数据库

## 4. 这台机器必须采用的轻量化策略

为了让系统在 `2C2G` 机器上更稳，当前项目已经建议使用以下参数：

- `GUNICORN_WORKERS=2`
- `CELERY_WORKER_CONCURRENCY=1`

原因：

- Gunicorn worker 过多会直接放大内存占用
- Celery 并发不需要高，当前项目异步量不大
- 单机环境下，优先保证稳定，而不是追求吞吐

## 5. 强烈建议先创建 Swap

如果不加 Swap，这台服务器在 `docker compose build` 或首次启动时更容易因为内存紧张被系统杀进程。

建议创建 2G Swap：

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h
```

如果 `fallocate` 不可用，可以改用：

```bash
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h
```

## 6. 域名和 IP 的使用建议

你当前有公网 IP，所以有两种上线方式：

### 方式 A：先用公网 IP 跑通

优点：

- 最快
- 不依赖域名和证书

适合：

- 先验收系统是否能正常启动
- 先完成答辩或内部测试

此时 `.env.production` 可先写成：

```env
DJANGO_ALLOWED_HOSTS=<你的公网IP>
DJANGO_CSRF_TRUSTED_ORIGINS=http://<你的公网IP>
CORS_ALLOWED_ORIGINS=http://<你的公网IP>
SESSION_COOKIE_SECURE=false
CSRF_COOKIE_SECURE=false
DJANGO_SECURE_SSL_REDIRECT=false
```

### 方式 B：绑定域名后再正式开放

优点：

- 后续更适合正式访问
- 可以继续接 HTTPS

适合：

- 真正准备对外使用

## 7. 阿里云安全组建议

放行：

- `22`，仅你的管理 IP 优先
- `80`
- `443`，如果后续上 HTTPS

不要放行：

- `5432`
- `6379`
- `8000`

## 8. 部署顺序建议

建议按以下顺序执行：

1. 登录服务器
2. 检查 Docker 是否可用
3. 创建 Swap
4. 上传或拉取项目代码
5. 配置 `.env.production`
6. 启动生产编排
7. 创建超级管理员
8. 先用 IP 验证首页、接口、后台
9. 再决定是否绑定域名和 HTTPS

## 9. 这台服务器上不建议做的事

当前阶段不建议：

- 同时跑太多非必要容器
- 暴露数据库和 Redis 到公网
- 在服务器上长期保留大量无用镜像和构建缓存
- 把 Gunicorn worker 开到 3 以上
- 把 Celery 并发开大

## 10. 当前建议结论

你的服务器配置可以部署当前系统，而且适合“全部服务同机部署”。

推荐路线是：

1. 先按公网 IP + HTTP 跑通系统
2. 确认前后端、数据库、报表、社区都正常
3. 再绑定域名
4. 最后再做 HTTPS 和更细的安全收口

这条路线风险最低，也最符合你当前项目阶段。
