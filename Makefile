PYTHON ?= python3
CLI = $(PYTHON) .claude/scripts/ph_cli.py

.PHONY: setup doctor test validate sample clean

setup:
	$(PYTHON) -m pip install -e '.[dev,mcp]'

doctor:
	$(CLI) doctor

validate:
	$(CLI) framework validate

test:
	$(PYTHON) -m unittest discover -s tests -v

sample:
	$(CLI) project init --project-id sample-logic-grids --topic "A progressive collection of logic-grid puzzles" --audience adult-general --product-type puzzle-book --formats paperback

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
