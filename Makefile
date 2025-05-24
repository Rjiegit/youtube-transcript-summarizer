.PHONY: install-dependencies run yt-dlp

install-dependencies:
	which brew >/dev/null 2>&1 || /bin/bash -c "$$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
	brew install yt-dlp
	pip install -r requirements.txt

run:
	python main.py

yt-dlp:
	yt-dlp -S "res:360" -o "data/videos/%(title)s.%(ext)s" $(url)