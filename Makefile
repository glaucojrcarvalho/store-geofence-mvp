# Makefile for common dev tasks
.PHONY: help build up migrate seed test-local test-container e2e clean-caches

help:
	@echo "Available targets:"
	@echo "  make build          Build the API Docker image"
	@echo "  make up             Start db and redis (detached)"
	@echo "  make migrate        Run alembic migrations"
	@echo "  make seed           Seed demo data"
	@echo "  make test-local     Run pytest locally (requires deps installed)"
	@echo "  make test-container Run pytest inside the api container (uses docker-compose)"
	@echo "  make e2e            Run the end-to-end test inside the api container"
	@echo "  make clean-caches   Remove pytest/ruff caches and recreate directories"

build:
	docker compose build api

up:
	docker compose up -d db redis

migrate:
	docker compose run --rm api alembic upgrade head

seed:
	docker compose run --rm api python -m scripts.seed

test-local:
	# runs pytest locally, ensure PYTHONPATH is set to the repo root
	PYTHONPATH=. pytest -q

test-container:
	# run tests inside the api container (docker-compose must be up)
	docker compose run --rm api pytest -q -r a

e2e: up migrate
	# run the dedicated e2e test (requires db + redis up and migrations applied)
	docker compose run --rm api pytest tests/test_e2e.py -q -r a

clean-caches:
	./scripts/clean_caches.sh

