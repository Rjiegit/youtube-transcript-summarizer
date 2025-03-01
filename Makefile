install-dependencies:
	pip install -r requirements.txt
.PHONY: install-dependencies

run:
	python main.py
.PHONY: run