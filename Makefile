.PHONY: install-dependencies run yt-dl

install-dependencies:
	which brew >/dev/null 2>&1 || /bin/bash -c "$$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
	pip install -r requirements.txt

run:
	python main.py

yt-dl:
	yt-dlp -S "res:360" -o "data/videos/%(title)s.%(ext)s" $(url)