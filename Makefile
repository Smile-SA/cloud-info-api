all: venv install

venv:
	python3.9 -m venv .venv

.PHONY: install
install: venv
	./.venv/bin/pip install -U pip wheel
	./.venv/bin/pip install -e .[dev]

.PHONY: clean
clean:
	rm -rf .pytest_cache .eggs *.egg-info
	find . -path ./.venv -prune -o -name "*.pyc" -o -name "*.pyo" -o -name "__pycache__" -print0 | xargs -r -0 rm -rv
	@echo "You may not want to remove ./.venv, please do it by hand." >&2