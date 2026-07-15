import logging
from src.database import USE_POSTGRES

logger = logging.getLogger(__name__)


def check_table_exists(conn, table_name: str) -> bool:
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute("SELECT to_regclass(%s)", (f"public.{table_name}",))
        res = cur.fetchone()[0]
        return res is not None
    else:
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        return cur.fetchone() is not None


def run_migrations(conn):
    cur = conn.cursor()

    # 1. Create schema_versions table
    if USE_POSTGRES:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_versions (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_versions (
                version INTEGER PRIMARY KEY,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    cur.execute("SELECT version FROM schema_versions WHERE version = 1")
    if cur.fetchone():
        return  # Already migrated

    urls_exists = check_table_exists(conn, "urls")
    links_exists = check_table_exists(conn, "links")

    # Determine if daily_stats currently references urls
    stats_ref_urls = False
    postgres_fk_constraints = []

    if USE_POSTGRES:
        # Check current foreign key targets for daily_stats in PostgreSQL
        cur.execute("""
            SELECT tc.constraint_name, ccu.table_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_name = 'daily_stats'
              AND tc.table_schema = 'public'
        """)
        fk_rows = cur.fetchall()
        for c_name, t_name in fk_rows:
            postgres_fk_constraints.append(c_name)
            if t_name == "urls":
                stats_ref_urls = True
    else:
        # Check current foreign key targets for daily_stats in SQLite
        if check_table_exists(conn, "daily_stats"):
            cur.execute("PRAGMA foreign_key_list(daily_stats)")
            fk_list = cur.fetchall()
            stats_ref_urls = any(row[2] == "urls" for row in fk_list)

    id_map = {}
    should_drop_urls = False

    # 2. Schema adaptation
    if urls_exists and not links_exists:
        # Simple Rename path
        if USE_POSTGRES:
            cur.execute("ALTER TABLE urls RENAME TO links")
        else:
            cur.execute("ALTER TABLE urls RENAME TO links")
        links_exists = True

    elif urls_exists and links_exists:
        # Merge path
        logger.warning(
            "Both 'urls' and 'links' tables exist. Performing merge migration."
        )
        should_drop_urls = True

    # 3. Add new columns to links and profiles before we select or update anything
    def add_column_if_not_exists(table, col, definition):
        if USE_POSTGRES:
            cur.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name=%s AND column_name=%s",
                (table, col),
            )
            if not cur.fetchone():
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")
        else:
            cur.execute(f"PRAGMA table_info({table})")
            cols = [r[1] for r in cur.fetchall()]
            if col not in cols:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")

    if links_exists:
        add_column_if_not_exists(
            "links", "profile_id", "INTEGER REFERENCES profiles(id) ON DELETE SET NULL"
        )
        add_column_if_not_exists("links", "title", "TEXT")
        if USE_POSTGRES:
            add_column_if_not_exists("links", "show_on_tree", "BOOLEAN DEFAULT FALSE")
        else:
            add_column_if_not_exists("links", "show_on_tree", "BOOLEAN DEFAULT 0")
        add_column_if_not_exists("links", "click_count", "INTEGER DEFAULT 0")
        if USE_POSTGRES:
            add_column_if_not_exists("links", "last_accessed", "TIMESTAMP")
        else:
            add_column_if_not_exists("links", "last_accessed", "DATETIME")

    if check_table_exists(conn, "profiles"):
        add_column_if_not_exists("profiles", "avatar_url", "TEXT")
        add_column_if_not_exists("profiles", "avatar_object_key", "TEXT")
        add_column_if_not_exists("profiles", "tree_views", "INTEGER DEFAULT 0")
        add_column_if_not_exists("profiles", "social_links", "TEXT")

    # 4. Perform Merge data copying if both tables exist
    if urls_exists and should_drop_urls:
        # Query columns on urls dynamically
        if USE_POSTGRES:
            cur.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name='urls'"
            )
            existing_urls_cols = {r[0] for r in cur.fetchall()}
        else:
            cur.execute("PRAGMA table_info(urls)")
            existing_urls_cols = {r[1] for r in cur.fetchall()}

        required_urls_cols = {"id", "short_code", "original_url"}
        missing_required_cols = required_urls_cols - existing_urls_cols
        if missing_required_cols:
            missing = ", ".join(sorted(missing_required_cols))
            raise RuntimeError(
                f"Legacy urls table is missing required columns: {missing}"
            )

        base_cols = ["id", "user_id", "short_code", "original_url", "created_at"]
        cols_to_select = [c for c in base_cols if c in existing_urls_cols]
        extra_cols = [
            "profile_id",
            "title",
            "show_on_tree",
            "click_count",
            "last_accessed",
        ]
        selected_extras = [c for c in extra_cols if c in existing_urls_cols]
        query_cols = cols_to_select + selected_extras

        cur.execute(f"SELECT {', '.join(query_cols)} FROM urls")
        old_urls = cur.fetchall()

        for row in old_urls:
            row_dict = dict(zip(query_cols, row))
            old_id = row_dict["id"]
            user_id = row_dict.get("user_id")
            short_code = row_dict["short_code"]
            orig_url = row_dict["original_url"]
            created_at = row_dict.get("created_at")

            profile_id = row_dict.get("profile_id", None)
            title = row_dict.get("title", None)
            show_on_tree = row_dict.get("show_on_tree", None)
            click_count = row_dict.get("click_count", 0)
            last_accessed = row_dict.get("last_accessed", None)

            # Check if short_code exists in links
            cur.execute(
                "SELECT id, profile_id, title, show_on_tree, click_count, last_accessed FROM links WHERE short_code = %s"
                if USE_POSTGRES
                else "SELECT id, profile_id, title, show_on_tree, click_count, last_accessed FROM links WHERE short_code = ?",
                (short_code,),
            )
            existing = cur.fetchone()

            if existing:
                (
                    ex_id,
                    ex_profile_id,
                    ex_title,
                    ex_show_on_tree,
                    ex_click_count,
                    ex_last_accessed,
                ) = existing
                id_map[old_id] = ex_id

                # Clicks sum
                new_click_count = (ex_click_count or 0) + (click_count or 0)

                # Last accessed max/preservation
                new_last_accessed = ex_last_accessed
                if not ex_last_accessed:
                    new_last_accessed = last_accessed
                elif last_accessed:
                    try:
                        new_last_accessed = max(ex_last_accessed, last_accessed)
                    except Exception:
                        pass

                # Preserve profile_id & title from urls if links is missing
                new_profile_id = (
                    ex_profile_id if ex_profile_id is not None else profile_id
                )
                new_title = ex_title if ex_title else title

                # Preserve show_on_tree ONLY when links' value is NULL
                new_show_on_tree = ex_show_on_tree
                if ex_show_on_tree is None:
                    new_show_on_tree = show_on_tree

                cur.execute(
                    "UPDATE links SET click_count = %s, last_accessed = %s, profile_id = %s, title = %s, show_on_tree = %s WHERE id = %s"
                    if USE_POSTGRES
                    else "UPDATE links SET click_count = ?, last_accessed = ?, profile_id = ?, title = ?, show_on_tree = ? WHERE id = ?",
                    (
                        new_click_count,
                        new_last_accessed,
                        new_profile_id,
                        new_title,
                        new_show_on_tree,
                        ex_id,
                    ),
                )
            else:
                # Insert into links
                if USE_POSTGRES:
                    cur.execute(
                        "INSERT INTO links (user_id, short_code, original_url, created_at, profile_id, title, show_on_tree, click_count, last_accessed) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                        (
                            user_id,
                            short_code,
                            orig_url,
                            created_at,
                            profile_id,
                            title,
                            show_on_tree,
                            click_count,
                            last_accessed,
                        ),
                    )
                    new_id = cur.fetchone()[0]
                else:
                    cur.execute(
                        "INSERT INTO links (user_id, short_code, original_url, created_at, profile_id, title, show_on_tree, click_count, last_accessed) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            user_id,
                            short_code,
                            orig_url,
                            created_at,
                            profile_id,
                            title,
                            show_on_tree,
                            click_count,
                            last_accessed,
                        ),
                    )
                    new_id = cur.lastrowid
                id_map[old_id] = new_id

    # 5. Process daily_stats data remapping & table rebuilding / recreation
    if check_table_exists(conn, "daily_stats"):
        cur.execute("SELECT id, link_id, date, clicks FROM daily_stats")
        stats_rows = cur.fetchall()

        mapped_stats = {}
        for s_id, l_id, dt, clk in stats_rows:
            target_link_id = l_id
            if stats_ref_urls:
                if id_map:
                    if l_id in id_map:
                        target_link_id = id_map[l_id]
                    else:
                        # Skip orphaned/deleted statistics
                        continue
                else:
                    target_link_id = l_id

            key = (target_link_id, dt)
            if key in mapped_stats:
                mapped_stats[key] = (mapped_stats[key][0], mapped_stats[key][1] + clk)
            else:
                mapped_stats[key] = (s_id, clk)

        if USE_POSTGRES:
            # PostgreSQL statistics migration
            from psycopg2.extensions import quote_ident

            for c_name in postgres_fk_constraints:
                cur.execute(
                    f"ALTER TABLE daily_stats DROP CONSTRAINT {quote_ident(c_name, conn)}"
                )

            # Clear stats table
            cur.execute("DELETE FROM daily_stats")

            # Re-insert merged stats preserving stat IDs
            for (link_id, date), (stat_id, clicks) in mapped_stats.items():
                cur.execute(
                    "INSERT INTO daily_stats (id, link_id, date, clicks) VALUES (%s, %s, %s, %s)",
                    (stat_id, link_id, date, clicks),
                )

            # Recreate PostgreSQL constraint pointing to links with ON DELETE CASCADE
            cur.execute("""
                ALTER TABLE daily_stats
                ADD CONSTRAINT daily_stats_link_id_fkey
                FOREIGN KEY (link_id) REFERENCES links(id) ON DELETE CASCADE
            """)
        else:
            # SQLite Rebuild Order:
            # 1. Rename daily_stats to old_daily_stats
            cur.execute("ALTER TABLE daily_stats RENAME TO old_daily_stats")

            # 2. Create new daily_stats table referencing links(id) ON DELETE CASCADE and UNIQUE(link_id, date)
            cur.execute("""
                CREATE TABLE daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    link_id INTEGER REFERENCES links(id) ON DELETE CASCADE,
                    date TEXT NOT NULL,
                    clicks INTEGER DEFAULT 0,
                    UNIQUE(link_id, date)
                )
            """)

            # 3. Copy remapped/merged data into the new daily_stats table
            for (link_id, date), (stat_id, clicks) in mapped_stats.items():
                cur.execute(
                    "INSERT INTO daily_stats (id, link_id, date, clicks) VALUES (?, ?, ?, ?)",
                    (stat_id, link_id, date, clicks),
                )

            # 4. Drop old_daily_stats
            cur.execute("DROP TABLE old_daily_stats")

    # 6. Cleanup old tables
    if should_drop_urls:
        cur.execute("DROP TABLE urls")

    # 7. PostgreSQL Sequence Reset after DML operations
    if USE_POSTGRES:
        cur.execute("""
            SELECT setval(
                pg_get_serial_sequence('links', 'id'),
                COALESCE(MAX(id), 1),
                MAX(id) IS NOT NULL
            ) FROM links;
        """)
        cur.execute("""
            SELECT setval(
                pg_get_serial_sequence('daily_stats', 'id'),
                COALESCE(MAX(id), 1),
                MAX(id) IS NOT NULL
            ) FROM daily_stats;
        """)

    # 8. Verification check of constraint Targets
    if check_table_exists(conn, "daily_stats"):
        if USE_POSTGRES:
            cur.execute("""
                SELECT ccu.table_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_name = 'daily_stats'
            """)
            targets = [r[0] for r in cur.fetchall()]
            if "links" not in targets:
                raise RuntimeError(
                    "PostgreSQL migration verification failed: daily_stats does not target links table."
                )
        else:
            cur.execute("PRAGMA foreign_key_list(daily_stats)")
            fk_list = cur.fetchall()
            targets = [row[2] for row in fk_list]
            if "links" not in targets:
                raise RuntimeError(
                    "SQLite migration verification failed: daily_stats does not target links table."
                )

            # SQLite constraint check
            cur.execute("PRAGMA foreign_key_check")
            fk_violations = cur.fetchall()
            if fk_violations:
                raise RuntimeError(
                    f"SQLite foreign key check failed with violations: {fk_violations}"
                )

    # 9. Record schema version
    cur.execute("INSERT INTO schema_versions (version) VALUES (1)")
