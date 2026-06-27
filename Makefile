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