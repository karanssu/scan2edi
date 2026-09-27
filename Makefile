.PHONY: setup up down logs test api backup

setup:
	@test -f .env || cp .env.example .env
	@echo "Edit .env, especially POSTGRES_PASSWORD and DATABASE_URL, before production use."

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

test:
	cd services/api && PYTHONPATH=. pytest -q

api:
	./infra/scripts/dev-api.sh

backup:
	./infra/scripts/backup.sh
