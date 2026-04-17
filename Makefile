.PHONY: dev-backend dev-frontend install setup

## Install Python deps
install:
	pip install -r requirements.txt

## Copy .env.example to .env (first-time setup)
setup:
	cp -n .env.example .env || true
	@echo "Edit .env with your FB token and admin password."

## Run backend dev server
dev-backend:
	uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

## Run frontend dev server
dev-frontend:
	cd frontend && npm run dev

## Run both (requires two terminals or use tmux)
dev:
	@echo "Start backend:  make dev-backend"
	@echo "Start frontend: make dev-frontend"

## Quick lint check
lint:
	cd frontend && npx eslint src/
