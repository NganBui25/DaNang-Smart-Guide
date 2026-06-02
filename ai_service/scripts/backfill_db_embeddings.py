"""
Backfill embedding_vector for approved places directly from ai_service.

Usage:
    python scripts/backfill_db_embeddings.py
"""

from __future__ import annotations

import json
import os
import sys

import mysql.connector
from dotenv import load_dotenv


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.embedder import get_embedding  # noqa: E402


load_dotenv()

PROGRESS_INTERVAL = int(os.getenv("BACKFILL_PROGRESS_INTERVAL", "20"))


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "danang_hidden_gems"),
    )


def _normalize_text(value) -> str:
    return str(value).strip() if value is not None else ""


def build_vectorize_text(row) -> str:
    return " ".join(
        filter(
            None,
            [
                _normalize_text(row.get("name")),
                _normalize_text(row.get("category_name")),
                _normalize_text(row.get("address")),
                _normalize_text(row.get("description")),
                _normalize_text(row.get("tag_names")),
            ],
        )
    )


def run() -> None:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM places_place
            WHERE status = 'APPROVED' AND embedding_vector IS NULL
            """.strip()
        )
        total = int(cursor.fetchone()["total"])
        if total == 0:
            print("[done] no places need backfill.")
            return

        print(f"[backfill] places to process: {total}")
        cursor.execute(
            """
            SELECT
                p.id,
                p.name,
                p.address,
                p.description,
                c.name AS category_name,
                GROUP_CONCAT(DISTINCT t.name SEPARATOR ' ') AS tag_names
            FROM places_place p
            LEFT JOIN places_category c ON c.id = p.category_id
            LEFT JOIN places_place_tags pt ON pt.place_id = p.id
            LEFT JOIN places_tag t ON t.id = pt.tag_id
            WHERE p.status = 'APPROVED' AND p.embedding_vector IS NULL
            GROUP BY p.id, p.name, p.address, p.description, c.name
            ORDER BY p.created_at ASC
            """.strip()
        )
        rows = cursor.fetchall()

        updated = 0
        for index, row in enumerate(rows, start=1):
            text = build_vectorize_text(row)
            vector = get_embedding(text)
            if not vector:
                continue

            cursor.execute(
                "UPDATE places_place SET embedding_vector = %s WHERE id = %s",
                (json.dumps(vector), row["id"]),
            )
            updated += 1

            if updated % PROGRESS_INTERVAL == 0:
                conn.commit()
                print(f"[backfill] updated {updated}/{total}")

        conn.commit()
        print(f"[done] embedding backfill completed: {updated}/{total}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    run()
