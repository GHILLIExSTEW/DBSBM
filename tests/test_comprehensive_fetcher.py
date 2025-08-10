import asyncio
import pytest
from bot.utils.comprehensive_fetcher import ComprehensiveFetcher

class DummyPool:
    pass

@pytest.mark.asyncio
async def test_comprehensive_fetcher_responses(monkeypatch):
    fetcher = ComprehensiveFetcher(DummyPool())
    # Monkeypatch the session and discovered_leagues for a controlled test
    class DummySession:
        async def get(self, url, headers=None, params=None):
            class DummyResponse:
                status = 200
                async def json(self):
                    return {"response": [{"id": 1}, {"id": 2}]}
                def raise_for_status(self):
                    pass
            return DummyResponse()
    fetcher.session = DummySession()
    fetcher.discovered_leagues = {"soccer": [{"id": 123, "name": "Test League"}]}
    results = await fetcher.fetch_all_leagues_data(date="2025-08-08", next_days=1)
    assert results["total_leagues"] == 1
    assert results["successful_fetches"] == 1
    assert results["failed_fetches"] == 0
    assert results["total_games"] == 2
