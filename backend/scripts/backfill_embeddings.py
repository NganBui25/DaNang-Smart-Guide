"""
Deprecated shim for the old backend-owned embedding backfill command.
"""

from __future__ import annotations


def run() -> int:
    print(
        "[deprecated] This script no longer generates embeddings from the backend container.\n"
        "[deprecated] Run the ai_service-owned command instead:\n"
        "docker compose -f docker-compose.yml -f docker-compose.gpu.yml run --rm "
        "ai_service python scripts/backfill_db_embeddings.py"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(run())
