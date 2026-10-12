from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "incident_lab.db"
SCHEMA = ROOT / "data" / "schema.sql"
SEED = ROOT / "data" / "seed.sql"

if DB.exists():
    DB.unlink()

conn = sqlite3.connect(DB)
conn.execute("PRAGMA foreign_keys = ON")
conn.executescript(SCHEMA.read_text())
conn.executescript(SEED.read_text())
conn.commit()

for table in ("incidents", "runbooks", "incident_runbooks"):
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table}: {count} rows")

conn.close()
print(f"database: {DB}")
