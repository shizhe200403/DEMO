.PHONY: check backend-check test migrate superuser docker-up docker-down docker-up-prod docker-down-prod

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
