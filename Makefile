SHELL := /bin/bash

.PHONY: up down build logs ps test reset-db

up:
	docker compose up -d --build

build:
	docker compose build

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

ps:
	docker compose ps -a

test:
	docker compose run --rm api pytest -q

reset-db:
	docker compose down -v
