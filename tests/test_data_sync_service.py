
import asyncio
import pytest
from bot.services.data_sync_service import DataSyncService
from bot.services.game_service import GameService
from bot.data.db_manager import DatabaseManager

@pytest.mark.asyncio
async def test_sync_games_postgres_syntax(monkeypatch):
    class DummyDBManager:
        async def fetch_all(self, query, args):
            # Should not raise syntax error
            assert "DATE_ADD" not in query
            assert "+ INTERVAL '72 hours'" in query
            # Simulate some games
            return [
                {"id": 1, "api_game_id": "g1", "start_time": "2025-08-08T20:00:00Z"},
                {"id": 2, "api_game_id": "g2", "start_time": "2025-08-08T22:00:00Z"},
            ]
    
    class DummyGameService:
        pass

    service = DataSyncService(DummyGameService(), DummyDBManager())
    count = await service.sync_games()
    assert count == 2
