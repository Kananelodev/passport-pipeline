# Convenience commands. Some targets call scripts YOU still have to write —
# they'll fail until the matching module is implemented. That's expected.

VENV=.venv
PY=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

.PHONY: setup seed run test clean shell

setup:              ## create venv + install deps
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "Done. Copy .env.example to .env, then run 'make seed'."

seed:               ## generate sample data (needs scripts/generate_sample_data.py)
	$(PY) scripts/generate_sample_data.py

run:               ## run the full pipeline end-to-end
	$(PY) -m passport_pipeline.pipeline

test:              ## run the test suite (red until you implement things)
	$(VENV)/bin/pytest -q

shell:             ## open a DuckDB SQL shell on the warehouse
	$(VENV)/bin/python -c "import duckdb,os; duckdb.connect(os.getenv('WAREHOUSE_PATH','data/warehouse/passport.duckdb')).sql('.tables')"

clean:             ## wipe generated data + warehouse (keeps .gitkeep)
	find data -type f ! -name '.gitkeep' -delete
	@echo "data/ cleared."
