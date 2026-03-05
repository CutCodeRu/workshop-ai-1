from __future__ import annotations

from psycopg import Connection


def upsert_document(conn: Connection, source_path: str, checksum: str) -> int:
    """Insert or update a KB document record and return its id."""
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO documents (source_path, checksum)
            VALUES (%s, %s)
            ON CONFLICT (source_path) DO UPDATE
            SET checksum = EXCLUDED.checksum,
                updated_at = NOW()
            RETURNING id;
            """,
            (source_path, checksum),
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Failed to upsert document.")
        return int(row[0])
