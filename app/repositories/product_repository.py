from typing import Optional

from app.db.database import get_connection


def create_product(
    name: str,
    description: str,
    value_proposition: Optional[str],
    target_problem: Optional[str],
) -> dict:
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO products (
                name,
                description,
                value_proposition,
                target_problem
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                description,
                value_proposition,
                target_problem,
            ),
        )

        product_id = cursor.lastrowid

        connection.commit()

        row = connection.execute(
            """
            SELECT
                id,
                name,
                description,
                value_proposition,
                target_problem,
                created_at
            FROM products
            WHERE id = ?
            """,
            (product_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()


def get_product(product_id: int) -> Optional[dict]:
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                id,
                name,
                description,
                value_proposition,
                target_problem,
                created_at
            FROM products
            WHERE id = ?
            """,
            (product_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()
