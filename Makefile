COMPOSE_FILE ?= docker-compose.yml
SERVICE ?= app
ALEMBIC ?= alembic
m ?= auto

PYTHON := python
PID_FILE := bot.pid
LOG_FILE := log_run.log
STOP_TIMEOUT := 5

.PHONY: up down logs ps restart stop migrate migrate-down revision history current stamp \
        revision_local migrate_local bot_run bot_run-log bot_run-tunnel bot_run-tunnel-log bot_stop install help

# -------- DOCKER --------
up:
	docker compose -f $(COMPOSE_FILE) up -d

down:
	docker compose -f $(COMPOSE_FILE) down -v

logs:
	docker compose -f $(COMPOSE_FILE) logs -f --tail=200

ps:
	docker compose -f $(COMPOSE_FILE) ps

restart:
	docker compose -f $(COMPOSE_FILE) restart

stop:
	docker compose -f $(COMPOSE_FILE) stop

# -------- MIGRATIONS (локально) --------
migrate: ## создать ревизию и сразу накатить (make migrate m="add wallets")
	$(ALEMBIC) revision --autogenerate -m "$(m)" && $(ALEMBIC) upgrade head

# -------- ЛОКАЛЬНЫЙ ЗАПУСК --------
install: ## установить зависимости
	pip install -r requirements.txt

bot_up: ## запустить проект с логированием в файл
	start /B $(PYTHON) run.py >> $(LOG_FILE) 2>&1

# -------- УТИЛИТЫ --------
status: ## показать статус процессов
	@tasklist /FI "IMAGENAME eq python.exe" 2>nul | findstr "python.exe" || echo "Проект не запущен"