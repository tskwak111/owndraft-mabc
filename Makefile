.PHONY: sync test lint typecheck evaluate export verify-export check

sync:
	uv sync --project apps/api --all-groups

test:
	uv run --project apps/api pytest

lint:
	uv run --project apps/api ruff check apps/api tests scripts

typecheck:
	uv run --project apps/api mypy apps/api/src

evaluate:
	uv run --project apps/api python -m owndraft.cli evaluate \
		--cases packages/evaluation/cases \
		--output artifacts/stage1/evaluation-final.json \
		--markdown artifacts/stage1/evaluation-final.md

export:
	uv run --project apps/api python scripts/export_timely_skill.py

verify-export:
	uv run --project apps/api python scripts/verify_timely_export.py \
		artifacts/stage1/owndraft-timely-skill.txt

check: test lint typecheck export verify-export
