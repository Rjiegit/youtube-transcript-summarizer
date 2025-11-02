.PHONY: install run yt-dlp auto test streamlit api docker-build docker-up docker-down

install:
	curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
	chmod a+rx /usr/local/bin/yt-dlp
	pip install -r requirements.txt

freeze:
	pip freeze > requirements.txt

run:
	python main.py

streamlit:
	streamlit run streamlit_app.py

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
