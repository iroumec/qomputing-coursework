PY := .venv/bin/python
REPORT ?= reports/qpe-grover/informe.qmd
SOURCE ?= images/logo-no-background.png
REPORTS_PY := reports/_scripts/reports.py

.PHONY: create-env freeze figures report reports report-new report-sync reports-list logos quarto-render quarto-preview

create-env:
	python3 -m venv .venv

freeze:
	$(PY) -m pip freeze > requirements.txt

# --- Informes ---------------------------------------------------------------
# make reports       Extrae figuras y compila todos los informes.
# make report        Extrae figuras y compila $(REPORT).
# make figures       Solo extrae las figuras de los notebooks de $(REPORT).
# make report-new    Crea reports/$(NAME)/ a partir de la plantilla común.
# make report-sync   Actualiza plantilla y logos (REPORT= para todos).
# make reports-list  Lista informes, notebooks y cantidad de figuras.
figures:
	$(PY) $(REPORTS_PY) figures $(REPORT)

# Importa el logo de portada desde images/ y lo propaga a los informes.
logos:
	$(PY) $(REPORTS_PY) logos --source "$(SOURCE)"

report: figures
	quarto render $(REPORT)

reports:
	$(PY) $(REPORTS_PY) figures
	@for report in reports/*/informe.qmd; do \
		echo "==> $$report"; \
		quarto render "$$report" || exit 1; \
	done

report-new:
	$(PY) $(REPORTS_PY) new "$(NAME)" --title "$(TITLE)" $(foreach nb,$(NOTEBOOKS),--notebook $(nb))

report-sync:
	$(PY) $(REPORTS_PY) sync $(REPORT)

reports-list:
	$(PY) $(REPORTS_PY) list

quarto-render:
	quarto render $(REPORT)

quarto-preview:
	quarto preview $(REPORT)
