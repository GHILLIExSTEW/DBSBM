import asyncio
import pytest
import asyncpg
from bot.utils.comprehensive_fetcher import ComprehensiveFetcher

@pytest.mark.asyncio
async def test_comprehensive_fetcher_real():
    # Connect to the real database using .env settings
    import os
    from dotenv import load_dotenv
    load_dotenv()
    db_pool = await asyncpg.create_pool(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
        host=os.getenv("POSTGRES_HOST"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        min_size=int(os.getenv("POSTGRES_POOL_MIN_SIZE", 1)),
        max_size=int(os.getenv("POSTGRES_POOL_MAX_SIZE", 10)),
    )
    async with db_pool:
        fetcher = ComprehensiveFetcher(db_pool)
        await fetcher.discover_all_leagues()
        results = await fetcher.fetch_all_leagues_data(date=None, next_days=1)
        print("Comprehensive fetch results:", results)
        print("\nHTTP status codes for each API call:")
        for entry in results.get("http_status_codes", []):
            print(f"Sport: {entry['sport']}, League: {entry['league']}, Date: {entry['date']}, Status: {entry['status_code']}")
        assert results["total_leagues"] > 0
        assert results["successful_fetches"] > 0
        # Not asserting total_games since it depends on live data
