PROJECT ?= demo
ENV_FILE ?= .env.production
PROD_COMPOSE = docker compose -p $(PROJECT) --env-file $(ENV_FILE) -f docker-compose.prod.yml

.PHONY: check backend-check test migrate superuser docker-up docker-down docker-up-prod docker-down-prod prod-build prod-up prod-recreate prod-ps prod-logs prod-health prod-migrate prod-superuser build-frontend-local deploy-frontend-dist

check:
	python3 -m py_compile $(shell rg --files backend -g '*.py')

backend-check:
	python3 -m py_compile $(shell rg --files backend -g '*.py')

test:
	docker compose run --rm backend python manage.py test backend.apps.common.tests

migrate:
	docker compose exec backend python manage.py migrate

superuser:
	docker compose exec backend python manage.py createsuperuser

docker-up:
	docker compose up --build

docker-down:
	docker compose down

docker-up-prod:
	docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build

docker-down-prod:
	docker compose --env-file .env.production -f docker-compose.prod.yml down

prod-build:
	DOCKER_BUILDKIT=1 $(PROD_COMPOSE) build backend frontend

prod-up:
	$(PROD_COMPOSE) up -d

prod-recreate:
	$(PROD_COMPOSE) up -d --build --force-recreate backend worker beat frontend

prod-ps:
	$(PROD_COMPOSE) ps

prod-logs:
	$(PROD_COMPOSE) logs -f $(svc)

prod-health:
	curl -fsS http://127.0.0.1/healthz
	curl -fsS http://127.0.0.1/api/v1/health/

prod-migrate:
	$(PROD_COMPOSE) exec backend python manage.py migrate

prod-superuser:
	$(PROD_COMPOSE) exec backend python manage.py createsuperuser

build-frontend-local:
	@echo "🔨 在本地构建前端..."
	cd frontend && npm install && npm run build
	@echo "✅ 构建完成! 文件在 frontend/dist/ 目录"

deploy-frontend-dist: build-frontend-local
	@echo "📤 上传到服务器..."
	@scp -r frontend/dist root@121.41.102.152:/tmp/frontend-dist
	@ssh root@121.41.102.152 "cd /root/demo-git && \
		docker compose -p demo --env-file .env.production -f docker-compose.prod.yml stop frontend && \
		mkdir -p frontend/dist && \
		rm -rf frontend/dist/* && \
		cp -r /tmp/frontend-dist/dist/* frontend/dist/ && \
		rm -rf /tmp/frontend-dist && \
		docker compose -p demo --env-file .env.production -f docker-compose.prod.yml start frontend"
	@echo "🎉 部署完成!"
