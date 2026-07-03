"""
migrate_mysql_to_pg.py
----------------------
Migrates all data from local MySQL -> Neon PostgreSQL.

Run BEFORE switching the app to PostgreSQL (while MySQL is still running).
Uses the MySQL credentials from .env (or override below) and the Neon URL.

Usage:
    python migrate_mysql_to_pg.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# MySQL source config
MYSQL_HOST     = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT     = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_DB       = os.getenv("MYSQL_DB", "car_travels")
MYSQL_USER     = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "NewStrongPassword@123")

# Neon PostgreSQL target
NEON_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://neondb_owner:npg_PY2uMVthA4CS@ep-cool-sun-at8dgj8e.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require",
)

try:
    import pymysql
    import pymysql.cursors
except ImportError:
    print("ERROR: pymysql is required for migration. Run: pip install pymysql")
    sys.exit(1)

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("ERROR: psycopg2-binary is required. Run: pip install psycopg2-binary")
    sys.exit(1)


def pg_connect(url: str):
    url = url.replace("postgresql+psycopg2://", "postgresql://")
    return psycopg2.connect(url)


def mysql_connect():
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor,
        charset="utf8mb4",
    )


def fetch_all(mysql_cur, table: str):
    mysql_cur.execute(f"SELECT * FROM `{table}`")
    return mysql_cur.fetchall()


def build_insert(table: str, row: dict) -> tuple:
    cols = list(row.keys())
    placeholders = ", ".join(["%s"] * len(cols))
    col_names = ", ".join([f'"{c}"' for c in cols])
    sql = f'INSERT INTO "{table}" ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'
    return sql, list(row.values())


# MySQL stores booleans as TINYINT (0/1); PostgreSQL needs True/False
BOOLEAN_COLUMNS = {
    "users":         {"is_active", "is_blocked"},
    "cars":          {"available", "is_deleted"},
    "bookings":      {"driver_required", "is_trip_completed", "is_rated"},
    "notifications": {"is_read"},
}


def migrate_table(mysql_cur, pg_cur, table: str):
    rows = fetch_all(mysql_cur, table)
    if not rows:
        print(f"  [{table}] -- 0 rows (empty, skipping)")
        return 0

    bool_cols = BOOLEAN_COLUMNS.get(table, set())
    inserted = 0
    for row in rows:
        clean = {}
        for k, v in row.items():
            if isinstance(v, (bytearray, bytes)):
                clean[k] = v.decode("utf-8", errors="replace")
            elif k in bool_cols and isinstance(v, int):
                clean[k] = bool(v)      # convert MySQL 0/1 -> Python True/False
            else:
                clean[k] = v
        sql, values = build_insert(table, clean)
        try:
            pg_cur.execute(sql, values)
            inserted += 1
        except Exception as e:
            print(f"    Warning: Row skipped in [{table}]: {e}")
            pg_cur.connection.rollback()

    print(f"  [{table}] -- {inserted}/{len(rows)} rows migrated OK")
    return inserted


TABLES_IN_ORDER = [
    "users",
    "cars",
    "car_images",
    "drivers",
    "bookings",
    "notifications",
    "tickets",
]


def reset_sequences(pg_cur):
    sequences = {
        "users":         ("id",        "users_id_seq"),
        "cars":          ("id",        "cars_id_seq"),
        "car_images":    ("id",        "car_images_id_seq"),
        "drivers":       ("id",        "drivers_id_seq"),
        "bookings":      ("id",        "bookings_id_seq"),
        "notifications": ("id",        "notifications_id_seq"),
        "tickets":       ("ticket_id", "tickets_ticket_id_seq"),
    }
    print("\nResetting PostgreSQL sequences...")
    for table, (col, seq) in sequences.items():
        sql = f"""
            SELECT setval(
                pg_get_serial_sequence('"{table}"', '{col}'),
                COALESCE((SELECT MAX("{col}") FROM "{table}"), 1)
            )
        """
        try:
            pg_cur.execute(sql)
            print(f"  Sequence reset for [{table}.{col}]")
        except Exception as e:
            print(f"  Warning: Could not reset sequence for [{table}]: {e}")
            pg_cur.connection.rollback()


def main():
    print("=" * 60)
    print("  CarTravels -- MySQL -> Neon PostgreSQL Data Migration")
    print("=" * 60)

    print(f"\nConnecting to MySQL ({MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB})...")
    try:
        mysql_conn = mysql_connect()
        mysql_cur = mysql_conn.cursor()
        print("  MySQL connected OK")
    except Exception as e:
        print(f"  MySQL connection failed: {e}")
        sys.exit(1)

    print(f"\nConnecting to Neon PostgreSQL...")
    try:
        pg_conn = pg_connect(NEON_URL)
        pg_conn.autocommit = False
        pg_cur = pg_conn.cursor()
        print("  Neon connected OK")
    except Exception as e:
        print(f"  Neon connection failed: {e}")
        mysql_conn.close()
        sys.exit(1)

    print("\nMigrating tables...\n")
    total_rows = 0

    # Tables are migrated in FK-safe dependency order
    # (parent tables first so FK constraints are always satisfied)
    for table in TABLES_IN_ORDER:
        try:
            count = migrate_table(mysql_cur, pg_cur, table)
            total_rows += count
            pg_conn.commit()
        except Exception as e:
            print(f"  Failed migrating [{table}]: {e}")
            pg_conn.rollback()

    reset_sequences(pg_cur)
    pg_conn.commit()

    print(f"\n{'=' * 60}")
    print(f"  Migration complete! Total rows migrated: {total_rows}")
    print(f"{'=' * 60}\n")

    mysql_cur.close()
    mysql_conn.close()
    pg_cur.close()
    pg_conn.close()


if __name__ == "__main__":
    main()
