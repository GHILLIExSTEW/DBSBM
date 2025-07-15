#!/usr/bin/env python3
"""
Database optimization script for DBSBM.
This script analyzes and optimizes database performance.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.db_manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Handles database optimization tasks."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def analyze_table_performance(self) -> Dict[str, Any]:
        """Analyze table performance and return recommendations."""
        logger.info("Analyzing table performance...")

        analysis = {"tables": {}, "recommendations": [], "indexes": {}}

        try:
            # Get table statistics
            tables = ["cappers", "bets", "games"]

            for table in tables:
                table_stats = await self._get_table_stats(table)
                analysis["tables"][table] = table_stats

                # Generate recommendations
                recommendations = await self._generate_table_recommendations(
                    table, table_stats
                )
                analysis["recommendations"].extend(recommendations)

            # Analyze indexes
            analysis["indexes"] = await self._analyze_indexes()

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing table performance: {e}")
            return analysis

    async def _get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """Get statistics for a specific table."""
        try:
            # Get row count
            row_count = await self.db_manager.fetch_one(
                f"SELECT COUNT(*) as count FROM {table_name}"
            )

            # Get table size
            table_size = await self.db_manager.fetch_one(
                """
                SELECT
                    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
                FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
                """,
                (self.db_manager.db_name, table_name),
            )

            # Get index information
            indexes = await self.db_manager.fetch_all(
                """
                SELECT
                    index_name,
                    column_name,
                    cardinality
                FROM information_schema.statistics
                WHERE table_schema = %s AND table_name = %s
                ORDER BY index_name, seq_in_index
                """,
                (self.db_manager.db_name, table_name),
            )

            return {
                "row_count": row_count["count"] if row_count else 0,
                "size_mb": table_size["size_mb"] if table_size else 0,
                "indexes": indexes,
            }

        except Exception as e:
            logger.error(f"Error getting stats for table {table_name}: {e}")
            return {}

    async def _generate_table_recommendations(
        self, table_name: str, stats: Dict[str, Any]
    ) -> List[str]:
        """Generate optimization recommendations for a table."""
        recommendations = []

        try:
            row_count = stats.get("row_count", 0)
            size_mb = stats.get("size_mb", 0)
            indexes = stats.get("indexes", [])

            # Check if table needs partitioning
            if row_count > 1000000:  # 1 million rows
                recommendations.append(
                    f"Consider partitioning table '{table_name}' (has {row_count:,} rows)"
                )

            # Check for missing indexes
            if table_name == "bets":
                if not any(idx["column_name"] == "guild_id" for idx in indexes):
                    recommendations.append(
                        "Add index on bets.guild_id for better query performance"
                    )
                if not any(idx["column_name"] == "user_id" for idx in indexes):
                    recommendations.append(
                        "Add index on bets.user_id for better query performance"
                    )
                if not any(idx["column_name"] == "created_at" for idx in indexes):
                    recommendations.append(
                        "Add index on bets.created_at for better date range queries"
                    )

            elif table_name == "cappers":
                if not any(idx["column_name"] == "guild_id" for idx in indexes):
                    recommendations.append(
                        "Add index on cappers.guild_id for better query performance"
                    )
                if not any(idx["column_name"] == "user_id" for idx in indexes):
                    recommendations.append(
                        "Add index on cappers.user_id for better query performance"
                    )

            elif table_name == "games":
                if not any(idx["column_name"] == "game_time" for idx in indexes):
                    recommendations.append(
                        "Add index on games.game_time for better date range queries"
                    )
                if not any(idx["column_name"] == "status" for idx in indexes):
                    recommendations.append(
                        "Add index on games.status for better status filtering"
                    )

            # Check for large table size
            if size_mb > 100:  # 100 MB
                recommendations.append(
                    f"Table '{table_name}' is large ({size_mb} MB). Consider archiving old data"
                )

        except Exception as e:
            logger.error(f"Error generating recommendations for {table_name}: {e}")

        return recommendations

    async def _analyze_indexes(self) -> Dict[str, Any]:
        """Analyze database indexes."""
        try:
            # Get unused indexes
            unused_indexes = await self.db_manager.fetch_all(
                """
                SELECT
                    table_name,
                    index_name,
                    cardinality
                FROM information_schema.statistics
                WHERE table_schema = %s
                AND cardinality = 0
                ORDER BY table_name, index_name
                """,
                (self.db_manager.db_name,),
            )

            # Get duplicate indexes
            duplicate_indexes = await self.db_manager.fetch_all(
                """
                SELECT
                    table_name,
                    GROUP_CONCAT(index_name) as indexes,
                    COUNT(*) as count
                FROM information_schema.statistics
                WHERE table_schema = %s
                GROUP BY table_name, column_name
                HAVING COUNT(*) > 1
                """,
                (self.db_manager.db_name,),
            )

            return {
                "unused_indexes": unused_indexes,
                "duplicate_indexes": duplicate_indexes,
            }

        except Exception as e:
            logger.error(f"Error analyzing indexes: {e}")
            return {}

    async def create_recommended_indexes(self) -> Dict[str, Any]:
        """Create recommended indexes for better performance."""
        logger.info("Creating recommended indexes...")

        results = {"created": [], "errors": []}

        try:
            # Indexes to create
            indexes_to_create = [
                ("bets", "idx_bets_guild_id", "guild_id"),
                ("bets", "idx_bets_user_id", "user_id"),
                ("bets", "idx_bets_created_at", "created_at"),
                ("bets", "idx_bets_status", "status"),
                ("cappers", "idx_cappers_guild_id", "guild_id"),
                ("cappers", "idx_cappers_user_id", "user_id"),
                ("games", "idx_games_game_time", "game_time"),
                ("games", "idx_games_status", "status"),
                ("games", "idx_games_sport_league", "sport, league"),
            ]

            for table, index_name, columns in indexes_to_create:
                try:
                    # Check if index already exists
                    existing = await self.db_manager.fetch_one(
                        """
                        SELECT COUNT(*) as count
                        FROM information_schema.statistics
                        WHERE table_schema = %s AND table_name = %s AND index_name = %s
                        """,
                        (self.db_manager.db_name, table, index_name),
                    )

                    if existing and existing["count"] == 0:
                        # Create index
                        await self.db_manager.execute(
                            f"CREATE INDEX {index_name} ON {table} ({columns})"
                        )
                        results["created"].append(f"{table}.{index_name}")
                        logger.info(f"Created index: {index_name} on {table}")
                    else:
                        logger.info(f"Index {index_name} already exists on {table}")

                except Exception as e:
                    error_msg = f"Error creating index {index_name} on {table}: {e}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)

            return results

        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            return results

    async def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """Clean up old data to improve performance."""
        logger.info(f"Cleaning up data older than {days_to_keep} days...")

        results = {"deleted_bets": 0, "deleted_games": 0, "errors": []}

        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            # Delete old bets
            deleted_bets = await self.db_manager.execute(
                "DELETE FROM bets WHERE created_at < %s", (cutoff_date,)
            )
            results["deleted_bets"] = (
                deleted_bets.get("affected_rows", 0) if deleted_bets else 0
            )

            # Delete old games
            deleted_games = await self.db_manager.execute(
                "DELETE FROM games WHERE game_time < %s AND status = 'finished'",
                (cutoff_date,),
            )
            results["deleted_games"] = (
                deleted_games.get("affected_rows", 0) if deleted_games else 0
            )

            logger.info(
                f"Deleted {results['deleted_bets']} old bets and {results['deleted_games']} old games"
            )

            return results

        except Exception as e:
            error_msg = f"Error cleaning up old data: {e}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
            return results

    async def optimize_tables(self) -> Dict[str, Any]:
        """Optimize tables for better performance."""
        logger.info("Optimizing tables...")

        results = {"optimized": [], "errors": []}

        try:
            tables = ["cappers", "bets", "games"]

            for table in tables:
                try:
                    await self.db_manager.execute(f"OPTIMIZE TABLE {table}")
                    results["optimized"].append(table)
                    logger.info(f"Optimized table: {table}")
                except Exception as e:
                    error_msg = f"Error optimizing table {table}: {e}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)

            return results

        except Exception as e:
            logger.error(f"Error optimizing tables: {e}")
            return results


async def main():
    """Main function to run database optimization."""
    logger.info("Starting database optimization...")

    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    # Create database manager
    db_manager = DatabaseManager()

    try:
        # Connect to database
        pool = await db_manager.connect()
        if not pool:
            logger.error("Failed to connect to database")
            return

        logger.info("Connected to database successfully")

        # Create optimizer
        optimizer = DatabaseOptimizer(db_manager)

        # Analyze performance
        logger.info("=" * 50)
        logger.info("ANALYZING DATABASE PERFORMANCE")
        logger.info("=" * 50)

        analysis = await optimizer.analyze_table_performance()

        # Print analysis results
        for table_name, stats in analysis["tables"].items():
            logger.info(f"\nTable: {table_name}")
            logger.info(f"  Rows: {stats.get('row_count', 0):,}")
            logger.info(f"  Size: {stats.get('size_mb', 0)} MB")
            logger.info(f"  Indexes: {len(stats.get('indexes', []))}")

        # Print recommendations
        if analysis["recommendations"]:
            logger.info("\nRECOMMENDATIONS:")
            for rec in analysis["recommendations"]:
                logger.info(f"  - {rec}")

        # Print index analysis
        if analysis["indexes"].get("unused_indexes"):
            logger.info("\nUNUSED INDEXES:")
            for idx in analysis["indexes"]["unused_indexes"]:
                logger.info(f"  - {idx['table_name']}.{idx['index_name']}")

        # Create recommended indexes
        logger.info("\n" + "=" * 50)
        logger.info("CREATING RECOMMENDED INDEXES")
        logger.info("=" * 50)

        index_results = await optimizer.create_recommended_indexes()
        if index_results["created"]:
            logger.info(f"Created {len(index_results['created'])} indexes")
        if index_results["errors"]:
            logger.info(f"Errors: {len(index_results['errors'])}")

        # Clean up old data
        logger.info("\n" + "=" * 50)
        logger.info("CLEANING UP OLD DATA")
        logger.info("=" * 50)

        cleanup_results = await optimizer.cleanup_old_data(days_to_keep=90)
        logger.info(f"Deleted {cleanup_results['deleted_bets']} old bets")
        logger.info(f"Deleted {cleanup_results['deleted_games']} old games")

        # Optimize tables
        logger.info("\n" + "=" * 50)
        logger.info("OPTIMIZING TABLES")
        logger.info("=" * 50)

        optimize_results = await optimizer.optimize_tables()
        if optimize_results["optimized"]:
            logger.info(f"Optimized {len(optimize_results['optimized'])} tables")

        logger.info("\n" + "=" * 50)
        logger.info("DATABASE OPTIMIZATION COMPLETE")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"Error during database optimization: {e}")
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
