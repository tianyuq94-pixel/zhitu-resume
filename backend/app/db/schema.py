"""Additive compatibility for installations using AUTO_CREATE_SCHEMA.

Never drops data or stamps Alembic history. Managed migrations remain preferred.
"""
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError


def ensure_profile_extensions(engine):
    additions = {
        "extra_facts": "JSON NULL",
        "facts_revision": "INTEGER NOT NULL DEFAULT 0",
    }
    if not inspect(engine).has_table("user_profiles"):
        return
    for name, definition in additions.items():
        if name in {column["name"] for column in inspect(engine).get_columns("user_profiles")}:
            continue
        try:
            with engine.begin() as connection:
                connection.execute(text(f"ALTER TABLE user_profiles ADD COLUMN {name} {definition}"))
        except DBAPIError:
            # Another cold start may have added the same column concurrently.
            if name not in {column["name"] for column in inspect(engine).get_columns("user_profiles")}:
                raise
