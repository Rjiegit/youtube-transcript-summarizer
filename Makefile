.PHONY: install run yt-dlp yt-dlp-update auto test streamlit api docker-build docker-up docker-down clear-processing-lock

YTDLP_AUTO_UPDATE ?= 1

PROCESSING_LOCK_HOST ?= http://localhost:8080
PROCESSING_LOCK_PAYLOAD ?= {"force":true,"force_threshold_seconds":0,"reason":"manual release via make clear-processing-lock"}

DOCKER_COMPOSE ?= $(shell if command -v docker-compose >/dev/null 2>&1; then echo docker-compose; else echo "docker compose"; fi)

install:
	curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
	chmod a+rx /usr/local/bin/yt-dlp
	uv sync --frozen --no-install-project

freeze:
	uv lock

run:
	uv run python -m src.apps.workers.cli --db-type sqlite

streamlit:
	uv run streamlit run src/apps/ui/streamlit_app.py

api:
	uv run uvicorn src.apps.api.main:app --reload --reload-dir /usr/src/app/src --host 0.0.0.0 --port 8080

test:
	uv run python -m unittest discover -s . -p "test*.py" -v

# Docker 相關命令
docker-build:
	DOCKER_BUILDKIT=1 $(DOCKER_COMPOSE) build

docker-up:
	DOCKER_BUILDKIT=1 $(DOCKER_COMPOSE) up --build

docker-down:
	$(DOCKER_COMPOSE) down

yt-dlp:
	yt-dlp -S "res:360" -o "data/videos/%(title)s.%(ext)s" $(url)

yt-dlp-update:
	@if [ "$(YTDLP_AUTO_UPDATE)" != "1" ]; then echo "Skip yt-dlp update (YTDLP_AUTO_UPDATE=$(YTDLP_AUTO_UPDATE))"; exit 0; fi
	curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
	chmod a+rx /usr/local/bin/yt-dlp
	yt-dlp --version

auto: yt-dlp run

clear-processing-lock:
	@token="$(PROCESSING_LOCK_ADMIN_TOKEN)"; \
	if [ -z "$$token" ] && [ -f .env ]; then \
		token="$$(grep -m1 '^PROCESSING_LOCK_ADMIN_TOKEN=' .env | cut -d'=' -f2-)"; \
	fi; \
	if [ -z "$$token" ]; then \
		echo "Set PROCESSING_LOCK_ADMIN_TOKEN via env or .env before calling this target."; \
		exit 1; \
	fi; \
	curl -sSf -X DELETE "$(PROCESSING_LOCK_HOST)/processing-lock" \
		-H "Content-Type: application/json" \
		-H "X-Maintainer-Token: $$token" \
		-d '$(PROCESSING_LOCK_PAYLOAD)'
