PYTHON ?= python3
VENV   := .venv
BIN    := $(VENV)/bin
export PYTHONPATH := src

.PHONY: help install install-dev demo collect pipeline all test notebook clean-outputs

help:
	@echo "make install    -> crée .venv et installe les dépendances"
	@echo "make demo       -> génère le jeu de démonstration (si aucune donnée réelle)"
	@echo "make collect    -> collecte réelle (France Travail, Adzuna, scraper JSON-LD)"
	@echo "make pipeline   -> nettoyage + NLP + SQLite + exports Tableau + rapport"
	@echo "make all        -> collect puis pipeline"
	@echo "make test       -> lance les tests"
	@echo "make notebook   -> réexécute le notebook d'exploration (après make install-dev)"

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt
	$(BIN)/pip install -e .

install-dev: install
	$(BIN)/pip install -r requirements-dev.txt

demo:
	$(BIN)/python -m jmi demo

collect:
	$(BIN)/python -m jmi collect

pipeline:
	$(BIN)/python -m jmi run

all: collect pipeline

test:
	$(BIN)/python -m pytest

notebook:
	$(BIN)/jupyter nbconvert --to notebook --execute --inplace notebooks/01_exploration_qualite.ipynb

# Supprime uniquement les sorties régénérables (jamais data/raw).
clean-outputs:
	rm -f data/processed/*.csv data/warehouse/*.db exports/tableau/*.csv
