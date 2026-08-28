import asyncio
import pytest
from unittest.mock import patch, AsyncMock

from mysite.asgi import application, lifespan


# ---------------------------------------------------------------------
# ROUTER STRUCTURE
# ---------------------------------------------------------------------

def test_asgi_application_has_correct_protocols():
    assert "http" in application.application_mapping
    assert "websocket" in application.application_mapping
    assert "lifespan" in application.application_mapping

    assert application.application_mapping["lifespan"] is lifespan


# ---------------------------------------------------------------------
# LIFESPAN: STARTUP + SHUTDOWN
# ---------------------------------------------------------------------

@pytest.mark.asyncio
async def test_lifespan_startup_and_shutdown_without_purge(monkeypatch):
    # Ensure purge is NOT triggered
    monkeypatch.setenv("RUN_PURGE_ON_STARTUP", "false")

    send = AsyncMock()
    receive = AsyncMock(side_effect=[
        {"type": "lifespan.shutdown"}
    ])

    await lifespan({"type": "lifespan"}, receive, send)

    # Startup complete must be sent
    send.assert_any_call({"type": "lifespan.startup.complete"})

    # Shutdown complete must be sent
    send.assert_any_call({"type": "lifespan.shutdown.complete"})


@pytest.mark.asyncio
async def test_lifespan_triggers_purge_when_env_true(monkeypatch):
    monkeypatch.setenv("RUN_PURGE_ON_STARTUP", "true")

    fake_task = AsyncMock()

    with patch("mysite.asgi.purge_all_rooms", new_callable=AsyncMock) as mock_purge:
        with patch("asyncio.create_task", return_value=fake_task) as mock_create_task:

            send = AsyncMock()
            receive = AsyncMock(side_effect=[
                {"type": "lifespan.shutdown"}
            ])

            await lifespan({"type": "lifespan"}, receive, send)

            # Was create_task called?
            mock_create_task.assert_called_once()

            # Was purge_all_rooms invoked to produce the coroutine?
            mock_purge.assert_called_once()

            # Startup + shutdown messages must be sent
            send.assert_any_call({"type": "lifespan.startup.complete"})
            send.assert_any_call({"type": "lifespan.shutdown.complete"})