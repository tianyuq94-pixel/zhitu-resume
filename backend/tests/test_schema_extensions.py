from sqlalchemy import create_engine, inspect, text
from app.db.schema import ensure_profile_extensions


def test_additive_schema_upgrade_preserves_old_records_and_is_repeatable():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE user_profiles (user_id INTEGER PRIMARY KEY, name TEXT)"))
        connection.execute(text("INSERT INTO user_profiles VALUES (1, 'existing')"))
    ensure_profile_extensions(engine)
    ensure_profile_extensions(engine)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT name, extra_facts, facts_revision FROM user_profiles")).one() == ('existing', None, 0)
    assert len(inspect(engine).get_columns('user_profiles')) == 4
