from pathlib import Path

from app.db import apply_migration

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "migrations"


if __name__ == "__main__":
    for migration in sorted(MIGRATIONS.glob("*.sql")):
        print(f"Applying {migration.name}")
        apply_migration(migration.read_text(encoding="utf-8"))
    print("Migrations applied successfully.")
