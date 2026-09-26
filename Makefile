# Convenience commands. Some targets call scripts YOU still have to write —
# they'll fail until the matching module is implemented. That's expected.

VENV=.venv
# Windows venvs put executables in Scripts/, POSIX in bin/.
ifeq ($(OS),Windows_NT)
BIN=$(VENV)/Scripts
else
BIN=$(VENV)/bin
endif
PY=$(BIN)/python
PIP=$(BIN)/pip
PYTEST=$(BIN)/pytest

.PHONY: setup seed run test clean shell

setup:
	python -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "Done. Copy .env.example to .env, then run 'make seed'."

seed:               ## generate sample data (needs scripts/generate_sample_data.py)
	$(PY) scripts/generate_sample_data.py

run:               ## run the full pipeline end-to-end
	$(PY) -m passport_pipeline.pipeline

test:              ## run the test suite (red until you implement things)
	$(PYTEST) -q

shell:             ## open a DuckDB SQL shell on the warehouse
	$(PY) -c "import duckdb,os; duckdb.connect(os.getenv('WAREHOUSE_PATH','data/warehouse/passport.duckdb')).sql('.tables')"

clean:             ## wipe generated data + warehouse (keeps .gitkeep)
	find data -type f ! -name '.gitkeep' -delete
	@echo "data/ cleared."
