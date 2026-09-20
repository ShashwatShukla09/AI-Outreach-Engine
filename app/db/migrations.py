from app.db.database import get_connection


def column_exists(
    table_name: str,
    column_name: str,
) -> bool:
    connection = get_connection()

    try:
        rows = connection.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()

        return any(
            row["name"] == column_name
            for row in rows
        )

    finally:
        connection.close()


def run_migrations() -> None:
    connection = get_connection()

    try:
        if not column_exists(
            "icps",
            "status",
        ):
            connection.execute(
                """
                ALTER TABLE icps
                ADD COLUMN status TEXT
                NOT NULL DEFAULT 'DRAFT'
                """
            )

        if not column_exists(
            "icps",
            "reviewed_at",
        ):
            connection.execute(
                """
                ALTER TABLE icps
                ADD COLUMN reviewed_at TEXT
                """
            )

        connection.commit()

    finally:
        connection.close()


if __name__ == "__main__":
    run_migrations()
    print("Database migrations completed successfully.")
