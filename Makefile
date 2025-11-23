.PHONY: install run yt-dlp auto test streamlit api docker-build docker-up docker-down clear-processing-lock

PROCESSING_LOCK_HOST ?= http://localhost:8080
PROCESSING_LOCK_PAYLOAD ?= {"force":true,"force_threshold_seconds":0,"reason":"manual release via make clear-processing-lock"}

install:
	curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
	chmod a+rx /usr/local/bin/yt-dlp
	pip install -r requirements.txt

freeze:
	pip freeze > requirements.txt

run:
	python -m src.apps.workers.cli --db-type sqlite

streamlit:
	streamlit run src/apps/ui/streamlit_app.py

api:
	uvicorn api.server:app --reload --reload-exclude ".git" --reload-exclude ".git/*" --host 0.0.0.0 --port 8080

test:
	python -m unittest discover -s . -p "test*.py" -v

# Docker 相關命令
docker-build:
	DOCKER_BUILDKIT=1 docker-compose build

docker-up:
	DOCKER_BUILDKIT=1 docker-compose up --build

docker-down:
	docker-compose down

yt-dlp:
	yt-dlp -S "res:360" -o "data/videos/%(title)s.%(ext)s" $(url)

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
