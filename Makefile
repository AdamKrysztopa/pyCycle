.PHONY: test lint format docs coverage

test:
	uv run testflo -n 1 pycycle --timeout=240 --show_skipped

lint:
	uv run ruff check .
	uv run flake8 .

format:
	uv run black .
	uv run isort .

docs:
	uv run make -C pycycle/docs html

coverage:
	uv run testflo -n 1 pycycle --coverage --coverpkg pycycle --durations=20
