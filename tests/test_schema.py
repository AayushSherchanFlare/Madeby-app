import re
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parents[1] / "database"


def test_schema_declares_expected_tables_and_triggers():
    schema = (DATABASE_DIR / "schema.sql").read_text(encoding="utf-8")

    assert len(re.findall(r"^CREATE TABLE ", schema, flags=re.MULTILINE)) == 10
    assert len(re.findall(r"^CREATE TRIGGER ", schema, flags=re.MULTILINE)) == 4
    assert "following_user_id" not in schema


def test_schema_omits_redundant_indexes():
    schema = (DATABASE_DIR / "schema.sql").read_text(encoding="utf-8")

    assert "idx_project_images_project" not in schema
    assert "idx_comments_project (" not in schema
    assert "idx_notifications_recipient (" not in schema


def test_category_seed_is_idempotent_and_complete():
    seed = (DATABASE_DIR / "seed.sql").read_text(encoding="utf-8")

    assert "INSERT IGNORE INTO categories" in seed
    assert len(re.findall(r"^\s+\('", seed, flags=re.MULTILINE)) == 9


def test_streamline_migration_is_restart_safe():
    migration = (
        DATABASE_DIR / "migrations" / "002_streamline_schema.sql"
    ).read_text(encoding="utf-8")

    assert "CREATE PROCEDURE migrate_002_streamline_schema()" in migration
    assert "IF EXISTS (" in migration
    assert "IF NOT EXISTS (" in migration
    assert "DROP PROCEDURE migrate_002_streamline_schema" in migration
