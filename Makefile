.PHONY: install run yt-dlp auto test streamlit

install:
	curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
	chmod a+rx /usr/local/bin/yt-dlp
	pip install -r requirements.txt

run:
	python main.py

streamlit:
	streamlit run streamlit_app.py

test:
	python -m unittest discover -s . -p "test*.py" -v

yt-dlp:
	yt-dlp -S "res:360" -o "data/videos/%(title)s.%(ext)s" $(url)

auto: yt-dlp run