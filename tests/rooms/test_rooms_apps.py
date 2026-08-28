import pytest
from unittest.mock import patch, MagicMock
from rooms.apps import RoomsConfig


@pytest.mark.parametrize("run_main", ["false", None])
def test_ready_skips_when_not_main(monkeypatch, run_main):
    if run_main is None:
        monkeypatch.delenv("RUN_MAIN", raising=False)
    else:
        monkeypatch.setenv("RUN_MAIN", run_main)
    monkeypatch.setenv("RUN_PURGE_ON_STARTUP", "true")
    

    with patch("rooms.services.purge_all_rooms") as mock_purge:
        with patch("threading.Thread") as mock_thread:
            RoomsConfig.ready(RoomsConfig)

            mock_purge.assert_not_called()
            mock_thread.assert_not_called()


def test_ready_runs_purge_thread(monkeypatch):
    monkeypatch.setenv("RUN_MAIN", "true")
    monkeypatch.setenv("RUN_PURGE_ON_STARTUP", "true")

    fake_thread = MagicMock()

    with patch("rooms.services.purge_all_rooms") as mock_purge:
        with patch("threading.Thread", return_value=fake_thread) as mock_thread:
            RoomsConfig.ready(RoomsConfig)

            mock_thread.assert_called_once()
            fake_thread.start.assert_called_once()


def test_ready_does_not_run_purge_if_env_false(monkeypatch):
    monkeypatch.setenv("RUN_MAIN", "true")
    monkeypatch.setenv("RUN_PURGE_ON_STARTUP", "false")

    with patch("rooms.services.purge_all_rooms") as mock_purge:
        with patch("threading.Thread") as mock_thread:
            RoomsConfig.ready(RoomsConfig)

            mock_purge.assert_not_called()
            mock_thread.assert_not_called()
