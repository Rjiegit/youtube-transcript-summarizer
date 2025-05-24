.PHONY: install run yt-dlp

install:
	pip install -r requirements.txt

run:
	python main.py

yt-dlp:
	yt-dlp -S "res:360" -o "data/videos/%(title)s.%(ext)s" $(url)