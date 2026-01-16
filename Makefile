.PHONY: up down build logs shell

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

log:
	docker compose logs -f

shell:
	docker compose exec bot /bin/bash

lock:
	docker compose run --rm bot uv lock

test:
	docker compose run --rm bot uv run python -m pytest
