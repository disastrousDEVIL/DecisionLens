.PHONY: api-test api-lint api-run web-install web-dev

api-test:
	cd backend && .venv/bin/pytest -q

api-lint:
	cd backend && .venv/bin/ruff check .

api-run:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

web-install:
	cd frontend && npm install

web-dev:
	cd frontend && npm run dev

