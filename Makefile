.PHONY: install install-hooks betterleaks-staged run rss-monitor rss-monitor-once yt-dlp yt-dlp-update auto test streamlit api showcase-install showcase-check showcase showcase-test docker-build docker-up docker-down cleanup-data-dry-run cleanup-data clear-processing-lock

YTDLP_AUTO_UPDATE ?= 1
VIDEO_RETENTION_DAYS ?= 7
SUMMARY_RETENTION_DAYS ?= 180

PROCESSING_LOCK_HOST ?= http://localhost:8080
PROCESSING_LOCK_PAYLOAD ?= {"force":true,"force_threshold_seconds":0,"reason":"manual release via make clear-processing-lock"}

DOCKER_COMPOSE ?= $(shell if command -v docker-compose >/dev/null 2>&1; then echo docker-compose; else echo "docker compose"; fi)

install:
	curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
	chmod a+rx /usr/local/bin/yt-dlp
	uv sync --frozen --no-install-project

install-hooks:
	./scripts/install-git-hooks.sh

betterleaks-staged:
	betterleaks git --staged --config .betterleaks-pre-commit.toml --redact --no-banner .

freeze:
	uv lock

run:
	uv run python -m src.apps.workers.cli --db-type sqlite

rss-monitor:
	uv run python -m src.apps.workers.rss_monitor

rss-monitor-once:
	uv run python -m src.apps.workers.rss_monitor --once

streamlit:
	uv run streamlit run src/apps/ui/streamlit_app.py

api:
	uv run uvicorn src.apps.api.main:app --reload --reload-dir /usr/src/app/src --host 0.0.0.0 --port 8080

showcase-install:
	npm --prefix frontend/nuxt-showcase install

showcase-check:
	npm --prefix frontend/nuxt-showcase run check-env

showcase:
	@env_file="frontend/nuxt-showcase/.env"; \
	if [ ! -f "$$env_file" ] && [ -f .env ]; then \
		env_file=".env"; \
	fi; \
	if [ -f "$$env_file" ]; then \
		while IFS= read -r line || [ -n "$$line" ]; do \
			case "$$line" in \
				''|\#*) continue ;; \
				*=*) export "$$line" ;; \
			esac; \
		done < "$$env_file"; \
	fi; \
	npm --prefix frontend/nuxt-showcase run dev

showcase-test:
	npm --prefix frontend/nuxt-showcase run test

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

cleanup-data-dry-run:
	@case "$(VIDEO_RETENTION_DAYS)" in ''|*[!0-9]*) echo "VIDEO_RETENTION_DAYS must be a non-negative integer."; exit 1 ;; esac
	@case "$(SUMMARY_RETENTION_DAYS)" in ''|*[!0-9]*) echo "SUMMARY_RETENTION_DAYS must be a non-negative integer."; exit 1 ;; esac
	@test -d data/videos -a -d data/summaries || { echo "Expected data/videos and data/summaries directories."; exit 1; }
	@video_minutes=$$(( $(VIDEO_RETENTION_DAYS) * 1440 )); \
		summary_minutes=$$(( $(SUMMARY_RETENTION_DAYS) * 1440 )); \
		find data/videos -type f -mmin +$$video_minutes -exec du -k {} + | \
		awk 'function human(kib) { if (kib >= 1048576) return sprintf("%.2f GiB", kib / 1048576); if (kib >= 1024) return sprintf("%.2f MiB", kib / 1024); return sprintf("%.0f KiB", kib) } { count++; kib += $$1 } END { printf "Videos eligible for cleanup: %d files, %s\n", count, human(kib) }'; \
		find data/summaries -type f -mmin +$$summary_minutes -exec du -k {} + | \
		awk 'function human(kib) { if (kib >= 1048576) return sprintf("%.2f GiB", kib / 1048576); if (kib >= 1024) return sprintf("%.2f MiB", kib / 1024); return sprintf("%.0f KiB", kib) } { count++; kib += $$1 } END { printf "Summaries eligible for cleanup: %d files, %s\n", count, human(kib) }'

cleanup-data:
	@case "$(VIDEO_RETENTION_DAYS)" in ''|*[!0-9]*) echo "VIDEO_RETENTION_DAYS must be a non-negative integer."; exit 1 ;; esac
	@case "$(SUMMARY_RETENTION_DAYS)" in ''|*[!0-9]*) echo "SUMMARY_RETENTION_DAYS must be a non-negative integer."; exit 1 ;; esac
	@test -d data/videos -a -d data/summaries || { echo "Expected data/videos and data/summaries directories."; exit 1; }
	@before_video_kib=$$(du -sk data/videos | awk '{ print $$1 }'); \
		before_summary_kib=$$(du -sk data/summaries | awk '{ print $$1 }'); \
		echo "Before cleanup:"; \
		awk -v video="$$before_video_kib" -v summary="$$before_summary_kib" 'function human(kib) { if (kib >= 1048576) return sprintf("%.2f GiB", kib / 1048576); if (kib >= 1024) return sprintf("%.2f MiB", kib / 1024); return sprintf("%.0f KiB", kib) } BEGIN { printf "  Videos: %s\n  Summaries: %s\n  Total: %s\n", human(video), human(summary), human(video + summary) }'; \
		video_minutes=$$(( $(VIDEO_RETENTION_DAYS) * 1440 )); \
		summary_minutes=$$(( $(SUMMARY_RETENTION_DAYS) * 1440 )); \
		find data/videos -type f -mmin +$$video_minutes -delete || exit 1; \
		find data/summaries -type f -mmin +$$summary_minutes -delete || exit 1; \
		after_video_kib=$$(du -sk data/videos | awk '{ print $$1 }'); \
		after_summary_kib=$$(du -sk data/summaries | awk '{ print $$1 }'); \
		echo "After cleanup:"; \
		awk -v video="$$after_video_kib" -v summary="$$after_summary_kib" 'function human(kib) { if (kib >= 1048576) return sprintf("%.2f GiB", kib / 1048576); if (kib >= 1024) return sprintf("%.2f MiB", kib / 1024); return sprintf("%.0f KiB", kib) } BEGIN { printf "  Videos: %s\n  Summaries: %s\n  Total: %s\n", human(video), human(summary), human(video + summary) }'; \
		reclaimed_kib=$$(( before_video_kib + before_summary_kib - after_video_kib - after_summary_kib )); \
		awk -v reclaimed="$$reclaimed_kib" 'function human(kib) { if (kib >= 1048576) return sprintf("%.2f GiB", kib / 1048576); if (kib >= 1024) return sprintf("%.2f MiB", kib / 1024); return sprintf("%.0f KiB", kib) } BEGIN { printf "Reclaimed: %s\n", human(reclaimed) }'

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
