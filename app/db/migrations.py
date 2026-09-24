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


def table_exists(
    table_name: str,
) -> bool:
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = ?
            """,
            (table_name,),
        ).fetchone()

        return row is not None

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

        if not table_exists(
            "outreach_attribution_snapshots"
        ):
            connection.execute(
                """
                CREATE TABLE outreach_attribution_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    outreach_message_id INTEGER NOT NULL UNIQUE,

                    product_id INTEGER,
                    product_name TEXT,

                    icp_id INTEGER,
                    icp_name TEXT,

                    market TEXT,
                    country TEXT,
                    industry TEXT,
                    business_model TEXT,
                    buyer_category TEXT,

                    signals_json TEXT NOT NULL DEFAULT '[]',

                    captured_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (outreach_message_id)
                        REFERENCES outreach_messages(id)
                        ON DELETE CASCADE,

                    FOREIGN KEY (product_id)
                        REFERENCES products(id)
                        ON DELETE SET NULL,

                    FOREIGN KEY (icp_id)
                        REFERENCES icps(id)
                        ON DELETE SET NULL
                )
                """
            )


        if not table_exists(
            "campaigns"
        ):
            connection.execute(
                """
                CREATE TABLE campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    product_id INTEGER NOT NULL,
                    icp_id INTEGER NOT NULL,

                    name TEXT NOT NULL,
                    market TEXT,

                    status TEXT NOT NULL DEFAULT 'DRAFT'
                        CHECK (
                            status IN (
                                'DRAFT',
                                'ACTIVE',
                                'PAUSED',
                                'COMPLETED'
                            )
                        ),

                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (product_id)
                        REFERENCES products(id)
                        ON DELETE CASCADE,

                    FOREIGN KEY (icp_id)
                        REFERENCES icps(id)
                        ON DELETE CASCADE
                )
                """
            )

        if not table_exists(
            "campaign_companies"
        ):
            connection.execute(
                """
                CREATE TABLE campaign_companies (
                    campaign_id INTEGER NOT NULL,
                    company_id INTEGER NOT NULL,

                    added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                    PRIMARY KEY (
                        campaign_id,
                        company_id
                    ),

                    FOREIGN KEY (campaign_id)
                        REFERENCES campaigns(id)
                        ON DELETE CASCADE,

                    FOREIGN KEY (company_id)
                        REFERENCES companies(id)
                        ON DELETE CASCADE
                )
                """
            )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_campaigns_product
            ON campaigns(product_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_campaigns_icp
            ON campaigns(icp_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_campaigns_status
            ON campaigns(status)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_campaign_companies_company
            ON campaign_companies(company_id)
            """
        )

        connection.commit()

    finally:
        connection.close()


if __name__ == "__main__":
    run_migrations()
    print("Database migrations completed successfully.")
