from app.db.database import get_connection


def create_tables() -> None:
    """
    Create all database tables and indexes required by the MVP.

    Running this function multiple times is safe because every table
    and index uses IF NOT EXISTS.
    """

    connection = get_connection()

    try:
        connection.executescript(
            """
            -- =========================================================
            -- 1. PRODUCTS
            -- What are we selling?
            -- =========================================================

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                name TEXT NOT NULL,
                description TEXT NOT NULL,
                value_proposition TEXT,
                target_problem TEXT,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );


            -- =========================================================
            -- 2. ICPs
            -- Who should buy the product?
            -- =========================================================

            CREATE TABLE IF NOT EXISTS icps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,

                name TEXT NOT NULL,

                industries TEXT,

                company_size_min INTEGER,
                company_size_max INTEGER,

                target_market TEXT NOT NULL,
                target_countries TEXT,

                business_models TEXT,
                buyer_categories TEXT,

                notes TEXT,

                status TEXT NOT NULL DEFAULT 'DRAFT',
                reviewed_at TEXT,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (product_id)
                    REFERENCES products(id)
                    ON DELETE CASCADE
            );


            -- =========================================================
            -- 3. COMPANIES
            -- Potential target accounts discovered for an ICP.
            -- =========================================================

            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                icp_id INTEGER NOT NULL,

                name TEXT NOT NULL,
                domain TEXT,

                country TEXT,
                market TEXT,

                industry TEXT,
                employee_count INTEGER,
                business_model TEXT,

                source TEXT,
                source_url TEXT,

                qualification_status TEXT NOT NULL DEFAULT 'UNREVIEWED',

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (icp_id)
                    REFERENCES icps(id)
                    ON DELETE CASCADE
            );


            -- =========================================================
            -- 4. COMPANY SCORES
            -- Explainable fit + intent scoring for each company.
            -- =========================================================

            CREATE TABLE IF NOT EXISTS company_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL UNIQUE,

                industry_score INTEGER NOT NULL DEFAULT 0,
                company_size_score INTEGER NOT NULL DEFAULT 0,
                geography_score INTEGER NOT NULL DEFAULT 0,
                business_model_score INTEGER NOT NULL DEFAULT 0,
                buyer_relevance_score INTEGER NOT NULL DEFAULT 0,

                intent_score INTEGER NOT NULL DEFAULT 0,
                data_confidence_score INTEGER NOT NULL DEFAULT 0,

                total_score INTEGER NOT NULL DEFAULT 0,
                priority TEXT NOT NULL DEFAULT 'UNRANKED',

                score_explanation TEXT,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (company_id)
                    REFERENCES companies(id)
                    ON DELETE CASCADE
            );


            -- =========================================================
            -- 5. SIGNALS
            -- Evidence that may indicate timing or buying intent.
            -- =========================================================

            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,

                signal_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,

                source TEXT,
                source_url TEXT,

                signal_date TEXT,
                confidence REAL,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (company_id)
                    REFERENCES companies(id)
                    ON DELETE CASCADE
            );


            -- =========================================================
            -- 6. ACCOUNT RESEARCH
            -- Why this company? Why now?
            -- =========================================================

            CREATE TABLE IF NOT EXISTS account_research (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL UNIQUE,

                company_summary TEXT,

                why_company TEXT,
                why_now TEXT,

                pain_points TEXT,
                relevant_evidence TEXT,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (company_id)
                    REFERENCES companies(id)
                    ON DELETE CASCADE
            );


            -- =========================================================
            -- 7. CONTACTS
            -- Potential decision-makers inside target companies.
            -- =========================================================

            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,

                first_name TEXT,
                last_name TEXT,

                job_title TEXT,
                buyer_category TEXT,

                email TEXT,
                linkedin_url TEXT,

                enrichment_provider TEXT,
                enrichment_status TEXT NOT NULL DEFAULT 'NOT_ENRICHED',

                relevance_score INTEGER NOT NULL DEFAULT 0,
                relevance_reason TEXT,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (company_id)
                    REFERENCES companies(id)
                    ON DELETE CASCADE
            );


            -- =========================================================
            -- 8. ENRICHMENT JOBS
            -- Tracks selective Clay/public/mock enrichment requests.
            -- =========================================================

            CREATE TABLE IF NOT EXISTS enrichment_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,

                provider TEXT NOT NULL,
                enrichment_type TEXT NOT NULL,

                status TEXT NOT NULL DEFAULT 'PENDING',

                requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,

                error_message TEXT,

                FOREIGN KEY (company_id)
                    REFERENCES companies(id)
                    ON DELETE CASCADE
            );


            -- =========================================================
            -- 9. OUTREACH MESSAGES
            -- AI-generated outreach with human approval.
            -- =========================================================

            CREATE TABLE IF NOT EXISTS outreach_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                company_id INTEGER NOT NULL,
                contact_id INTEGER,

                channel TEXT NOT NULL DEFAULT 'EMAIL',

                subject TEXT,
                message_body TEXT NOT NULL,

                personalisation_reason TEXT,

                status TEXT NOT NULL DEFAULT 'DRAFT',

                approved_at TEXT,
                rejected_at TEXT,
                sent_at TEXT,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (company_id)
                    REFERENCES companies(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (contact_id)
                    REFERENCES contacts(id)
                    ON DELETE SET NULL
            );


            -- =========================================================
            -- 10. OUTREACH EVENTS
            -- What happened after outreach?
            -- =========================================================

            CREATE TABLE IF NOT EXISTS outreach_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                outreach_message_id INTEGER NOT NULL,

                event_type TEXT NOT NULL,
                event_data TEXT,

                occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (outreach_message_id)
                    REFERENCES outreach_messages(id)
                    ON DELETE CASCADE
            );


            -- =========================================================
            -- INDEXES
            -- Improve common lookup/filter operations.
            -- =========================================================

            CREATE INDEX IF NOT EXISTS idx_companies_icp
            ON companies(icp_id);

            CREATE INDEX IF NOT EXISTS idx_companies_domain
            ON companies(domain);

            CREATE INDEX IF NOT EXISTS idx_companies_qualification
            ON companies(qualification_status);


            CREATE INDEX IF NOT EXISTS idx_scores_priority
            ON company_scores(priority);

            CREATE INDEX IF NOT EXISTS idx_scores_total
            ON company_scores(total_score);


            CREATE INDEX IF NOT EXISTS idx_signals_company
            ON signals(company_id);


            CREATE INDEX IF NOT EXISTS idx_contacts_company
            ON contacts(company_id);

            CREATE INDEX IF NOT EXISTS idx_contacts_buyer_category
            ON contacts(buyer_category);


            CREATE INDEX IF NOT EXISTS idx_enrichment_company
            ON enrichment_jobs(company_id);

            CREATE INDEX IF NOT EXISTS idx_enrichment_status
            ON enrichment_jobs(status);


            CREATE INDEX IF NOT EXISTS idx_outreach_company
            ON outreach_messages(company_id);

            CREATE INDEX IF NOT EXISTS idx_outreach_status
            ON outreach_messages(status);


            CREATE INDEX IF NOT EXISTS idx_outreach_events_message
            ON outreach_events(outreach_message_id);
            """
        )

        connection.commit()

    finally:
        connection.close()


if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully.")
