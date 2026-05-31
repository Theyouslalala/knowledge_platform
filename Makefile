.PHONY: install run test lint clean

install:
	conda env create -f environment.yml || conda env update -f environment.yml
	conda run -n knowledge_platform pip install -e ".[dev]"

run:
	conda run -n knowledge_platform uvicorn src.knowledge_platform.main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	conda run -n knowledge_platform python -m src.knowledge_platform.frontend.app

test:
	conda run -n knowledge_platform pytest tests/ -v

lint:
	conda run -n knowledge_platform ruff check src/ tests/
	conda run -n knowledge_platform ruff format --check src/ tests/

format:
	conda run -n knowledge_platform ruff check --fix src/ tests/
	conda run -n knowledge_platform ruff format src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf data/ *.egg-info/ dist/ build/
