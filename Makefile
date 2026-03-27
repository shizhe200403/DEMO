PROJECT ?= demo
ENV_FILE ?= .env.production
PROD_COMPOSE = docker compose -p $(PROJECT) --env-file $(ENV_FILE) -f docker-compose.prod.yml

.PHONY: check backend-check test migrate superuser docker-up docker-down docker-up-prod docker-down-prod prod-build prod-up prod-recreate prod-ps prod-logs prod-health prod-migrate prod-superuser

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
