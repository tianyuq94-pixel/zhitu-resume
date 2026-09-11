from hashlib import sha256
from time import time
from fastapi import HTTPException
from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError
from app.models.agent import AgentBudget


def check_budget(database, key: str, *, limit: int, window_seconds: int) -> None:
    """Database-backed fixed windows survive worker restarts and serverless instances."""
    now = int(time())
    bucket = now // window_seconds
    identity = sha256(key.encode()).hexdigest() + ':' + str(bucket)
    if database.get(AgentBudget, identity) is None:
        try:
            with database.begin_nested():
                database.add(AgentBudget(key=identity, count=0, expires_at=(bucket + 1) * window_seconds))
                database.flush()
        except IntegrityError:
            pass  # Another worker created the same counter.
    changed = database.execute(update(AgentBudget).where(AgentBudget.key == identity,
        AgentBudget.count < limit).values(count=AgentBudget.count + 1))
    if changed.rowcount != 1:
        database.rollback()
        raise HTTPException(429, '本时段使用次数已达上限，请稍后再试')
    database.execute(delete(AgentBudget).where(AgentBudget.expires_at < now - 86400))
    database.commit()
