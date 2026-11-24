

create-env:
	python3 -m venv .venv

freeze:
	.venv/bin/pip freeze > requirements.txt

quarto-render:
	quarto render reports/informe.qmd

quarto-preview:
	quarto preview reports/informe.qmd