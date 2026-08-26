import pytest
import logging
from core.consumers import safe_redis

@pytest.mark.asyncio
async def test_safe_redis_success():
    async def ok():
        return 123

    result = await safe_redis(ok())
    assert result == 123


@pytest.mark.asyncio
async def test_safe_redis_failure(caplog):
    async def bad():
        raise RuntimeError("boom")

    caplog.set_level(logging.ERROR, logger="redis")

    result = await safe_redis(bad(), fallback="fallback")
    assert result == "fallback"

    assert any("Redis error" in rec.message for rec in caplog.records)
