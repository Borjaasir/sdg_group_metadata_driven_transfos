.DEFAULT_GOAL := help
.PHONY: help install init

help:
	@echo "Available make targets:"
	@echo "  install     Install system tools and Poetry via pipx"
	@echo "  venv_init   Create a Python virtual environment at .venv and open bash with it activated"
	@echo "  python_deps Install dependencies with Poetry"
	@echo "  full_init   Run system deps, create venv, and install Python deps"
	@echo "  help        Show this help message"

system_deps:
	sudo apt install python3-pip \
	&& sudo apt install pipx \
	&& sudo snap install duckdb \
	&& pipx install poetry \
	&& pipx ensurepath
	@echo "Relog with your user to be able to solve poetry binary which was just added to your PATH"

venv_init:
	@echo "Creating virtual environment with python3.10..."
	python3.10 -m venv .venv

python_deps:
	@echo "Installing Python dependencies..."
	poetry lock
	poetry install
	@echo "Python dependencies installed"

full_init: system_deps venv_init python_deps
	@echo "Full initialization complete"
	@echo "Remember to activate your virtual environment, 'source .venv/bin/activate'"

airflow_run:
	docker compose up

pytest:
	pytest tests/test_population_data.py -v -s

duckdb_check: ## Gormaz 14 total_ambos_sexos in 2025, 18 in 2024
	duckdb data/output/warehouse.duckdb "SELECT COUNT(*) FROM raw_demo;" \
	&& duckdb data/output/warehouse.duckdb "SELECT * FROM demo WHERE municipio = '42097 Gormaz';" 

files_check: ## Last file and historic files (partitioned) should have 15410 entries for 2024 and 2025
	echo "Last file:" \
	&& python -c "import pandas as pd; print(pd.read_parquet('data/output/last.parquet').head())" \
	&& python -c "import pandas as pd; print('Entries:', len(pd.read_parquet('data/output/last.parquet')))" \
	&& echo "Historic files (partitioned):" \
	&& python -c "import pandas as pd, glob; df = pd.concat([pd.read_parquet(f) for f in glob.glob('data/output/historic/**/*.parquet', recursive=True)], ignore_index=True); print(df.head())" \
	&& python -c "import pandas as pd, glob; df = pd.concat([pd.read_parquet(f) for f in glob.glob('data/output/historic/**/*.parquet', recursive=True)], ignore_index=True); print('Entries:', len(df))"

local_run:
	poetry run python main.py