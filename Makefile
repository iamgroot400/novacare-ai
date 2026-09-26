SHELL := /bin/bash
COMPOSE := docker compose

.PHONY: help setup env dev seed test test-ai up down restart logs models smoke build clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

env: ## Create .env from .env.example if missing
	@test -f .env || (cp .env.example .env && echo "Created .env — review it")

setup: env ## Local dev setup (python venv + npm install)
	python -m venv backend/.venv
	backend/.venv/bin/pip install -U pip
	backend/.venv/bin/pip install -r backend/requirements.txt
	cd frontend && npm install
	@echo "Setup done. Set GROQ_API_KEY in .env, then 'make up' or run services individually."

seed: ## Seed / re-seed the demo database (idempotent)
	cd backend && ../backend/.venv/bin/python ../scripts/seed.py || python ../scripts/seed.py

dev: ## Run backend + frontend + voice locally (needs GROQ_API_KEY)
	@echo "Run these in separate terminals:"
	@echo "  1) cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000"
	@echo "  2) cd voice   && uvicorn server:app --reload --port 8080"
	@echo "  3) cd frontend && npm run dev"

test: ## Run backend unit tests (core, no Groq key needed)
	cd backend && (.venv/bin/python -m pytest -q tests/test_store_service.py tests/test_api.py || python -m pytest -q tests/test_store_service.py tests/test_api.py)

test-ai: ## Run RAG + agent tests (needs GROQ_API_KEY)
	cd backend && RUN_AGENT_SMOKE=1 python -m pytest -q

build: ## Build all Docker images
	$(COMPOSE) build

up: ## Start the full stack (docker compose)
	$(COMPOSE) up -d
	@echo "Starting... open http://localhost:3000/support when healthy."

down: ## Stop the stack
	$(COMPOSE) down

restart: down up ## Restart the stack

logs: ## Tail logs
	$(COMPOSE) logs -f --tail=100

models: ## Rebuild the RAG index
	bash scripts/init_models.sh

smoke: ## Run the end-to-end smoke test against the running stack
	python scripts/smoke_test.py

turn: ## Start the stack WITH the self-hosted coturn TURN server
	$(COMPOSE) --profile turn up -d

clean: ## Stop and remove volumes (DELETES demo data + models)
	$(COMPOSE) down -v
