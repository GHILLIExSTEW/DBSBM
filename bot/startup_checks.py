"""
Startup checks for DBSBM bot.
This module provides comprehensive startup validation for the Discord bot.
"""

import asyncio
import logging
import os
import sys
from typing import List, Dict, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class DBSBMStartupChecker:
    """Comprehensive startup checker for DBSBM bot."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.checks_passed = 0
        self.total_checks = 0
    
    async def run_all_checks(self) -> Tuple[bool, List[str]]:
        """Run all startup checks and return success status and errors."""
        logger.info("🔍 Running comprehensive startup checks...")
        
        # Reset counters
        self.errors = []
        self.warnings = []
        self.checks_passed = 0
        self.total_checks = 0
        
        # Run all checks
        await self._check_environment_variables()
        await self._check_discord_token()
        await self._check_database_connection()
        await self._check_api_connection()
        await self._check_file_permissions()
        await self._check_dependencies()
        
        # Log results
        logger.info(f"✅ Startup checks completed: {self.checks_passed}/{self.total_checks} passed")
        if self.warnings:
            logger.warning(f"⚠️ {len(self.warnings)} warnings found")
        if self.errors:
            logger.error(f"❌ {len(self.errors)} errors found")
        
        return len(self.errors) == 0, self.errors
    
    async def _check_environment_variables(self):
        """Check that all required environment variables are set."""
        self.total_checks += 1
        
        required_vars = [
            "DISCORD_TOKEN",
            "API_KEY", 
            "MYSQL_HOST",
            "MYSQL_USER",
            "MYSQL_PASSWORD",
            "MYSQL_DB",
            "TEST_GUILD_ID"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
        else:
            self.checks_passed += 1
            logger.info("✅ All required environment variables are set")
    
    async def _check_discord_token(self):
        """Validate Discord token format."""
        self.total_checks += 1
        
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            error_msg = "Discord token is not set"
            self.errors.append(error_msg)
            logger.error(error_msg)
            return
        
        # Basic format validation
        if not token.startswith("MT") or len(token) < 50:
            error_msg = "Discord token format appears invalid"
            self.errors.append(error_msg)
            logger.error(error_msg)
            return
        
        self.checks_passed += 1
        logger.info("✅ Discord token format appears valid")
    
    async def _check_database_connection(self):
        """Test database connection."""
        self.total_checks += 1
        
        try:
            import aiomysql
            
            # Test connection with timeout
            conn = await asyncio.wait_for(
                aiomysql.connect(
                    host=os.getenv("MYSQL_HOST"),
                    port=int(os.getenv("MYSQL_PORT", 3306)),
                    user=os.getenv("MYSQL_USER"),
                    password=os.getenv("MYSQL_PASSWORD"),
                    db=os.getenv("MYSQL_DB"),
                    autocommit=True
                ),
                timeout=10.0
            )
            await conn.ensure_closed()
            self.checks_passed += 1
            logger.info("✅ Database connection successful")
            
        except Exception as e:
            error_msg = f"Database connection failed: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
    
    async def _check_api_connection(self):
        """Test API connection."""
        self.total_checks += 1
        
        try:
            import aiohttp
            
            api_key = os.getenv("API_KEY")
            if not api_key:
                error_msg = "API key is not set"
                self.errors.append(error_msg)
                logger.error(error_msg)
                return
            
            # Test API with a simple request
            async with aiohttp.ClientSession() as session:
                # Use a simple endpoint to test connectivity
                test_url = "https://v3.football.api-sports.io/status"
                headers = {"x-rapidapi-key": api_key}
                
                async with session.get(test_url, headers=headers) as response:
                    if response.status == 200:
                        self.checks_passed += 1
                        logger.info("✅ API connection successful")
                    else:
                        error_msg = f"API connection failed with status {response.status}"
                        self.errors.append(error_msg)
                        logger.error(error_msg)
                        
        except Exception as e:
            error_msg = f"API connection test failed: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
    
    async def _check_file_permissions(self):
        """Check file permissions for critical directories."""
        self.total_checks += 1
        
        critical_dirs = [
            "data",
            "logs", 
            "static",
            "templates"
        ]
        
        missing_dirs = []
        for dir_name in critical_dirs:
            if not os.path.exists(dir_name):
                missing_dirs.append(dir_name)
        
        if missing_dirs:
            warning_msg = f"Missing directories: {', '.join(missing_dirs)}"
            self.warnings.append(warning_msg)
            logger.warning(warning_msg)
        else:
            self.checks_passed += 1
            logger.info("✅ All critical directories exist")
    
    async def _check_dependencies(self):
        """Check that all required dependencies are available."""
        self.total_checks += 1
        
        required_modules = [
            "discord",
            "aiomysql", 
            "aiohttp",
            "asyncio",
            "logging"
        ]
        
        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            error_msg = f"Missing required modules: {', '.join(missing_modules)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
        else:
            self.checks_passed += 1
            logger.info("✅ All required dependencies are available") 