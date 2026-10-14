.PHONY: help install run build up down logs restart clean

help:
	@echo "Targets:"
	@echo "  install  - pip install -r requirements.txt"
	@echo "  run      - run the MCP server locally (python server.py)"
	@echo "  build    - docker compose build"
	@echo "  up       - docker compose up -d"
	@echo "  down     - docker compose down"
	@echo "  logs     - docker compose logs -f"
	@echo "  restart  - docker compose down && docker compose up -d --build"
	@echo "  clean    - docker compose down --rmi local -v"

install:
	pip install -r requirements.txt

run:
	python server.py

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

restart: down
	docker compose up -d --build

clean:
	docker compose down --rmi local -v
