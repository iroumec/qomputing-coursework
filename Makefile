

create-env:
	python3 -m venv .venv

freeze:
	.venv/bin/pip freeze > requirements.txt