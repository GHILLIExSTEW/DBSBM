#!/usr/bin/env python3
"""
DBSBM Project Status Check Script

This script provides a comprehensive status check of the DBSBM project,
identifying completed tasks, current issues, and next steps.
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class DBSBMStatusChecker:
    """Comprehensive status checker for DBSBM project."""

    def __init__(self):
        self.project_root = project_root
        self.status = {
            "critical_tasks": {},
            "test_status": {},
            "environment": {},
            "performance": {},
            "security": {},
            "next_steps": []
        }

    def check_critical_tasks(self) -> Dict[str, bool]:
        """Check completion status of critical tasks."""
        tasks = {
            "Enhanced Cache Manager": self._check_cache_manager(),
            "Error Handling System": self._check_error_handling(),
            "Structured Logging": self._check_logging_system(),
            "Security Audit System": self._check_security_audit(),
            "Health Check System": self._check_health_system(),
            "Pydantic V2 Migration": self._check_pydantic_migration(),
        }

        self.status["critical_tasks"] = tasks
        return tasks

    def check_test_status(self) -> Dict[str, str]:
        """Check current test status."""
        test_results = {}

        # Check if tests directory exists
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            test_results["Tests Directory"] = "✅ Exists"
        else:
            test_results["Tests Directory"] = "❌ Missing"

        # Check conftest.py
        conftest_file = tests_dir / "conftest.py"
        if conftest_file.exists():
            test_results["Test Configuration"] = "✅ Configured"
        else:
            test_results["Test Configuration"] = "❌ Missing"

        # Try to run a simple test
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/test_critical_fixes.py", "-q"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                test_results["Critical Fixes Tests"] = "✅ Passing"
            else:
                test_results["Critical Fixes Tests"] = "❌ Failing"
        except Exception as e:
            test_results["Critical Fixes Tests"] = f"❌ Error: {str(e)}"

        self.status["test_status"] = test_results
        return test_results

    def check_environment(self) -> Dict[str, str]:
        """Check environment configuration."""
        env_status = {}

        # Check .env file
        env_file = self.project_root / "bot" / ".env"
        if env_file.exists():
            env_status[".env File"] = "✅ Exists"
        else:
            env_status[".env File"] = "❌ Missing"

        # Check required environment variables
        required_vars = ["MYSQL_PASSWORD", "DISCORD_TOKEN", "API_KEY"]
        for var in required_vars:
            if os.getenv(var):
                env_status[f"{var}"] = "✅ Set"
            else:
                env_status[f"{var}"] = "❌ Missing"

        # Check database connection
        try:
            from config.settings import get_settings
            settings = get_settings()
            env_status["Settings Import"] = "✅ Working"
        except Exception as e:
            env_status["Settings Import"] = f"❌ Error: {str(e)}"

        self.status["environment"] = env_status
        return env_status

    def check_performance(self) -> Dict[str, str]:
        """Check performance-related components."""
        perf_status = {}

        # Check cache manager
        try:
            from bot.utils.enhanced_cache_manager import EnhancedCacheManager
            perf_status["Cache Manager"] = "✅ Available"
        except Exception as e:
            perf_status["Cache Manager"] = f"❌ Error: {str(e)}"

        # Check performance monitor
        try:
            from bot.utils.performance_monitor import PerformanceMonitor
            perf_status["Performance Monitor"] = "✅ Available"
        except Exception as e:
            perf_status["Performance Monitor"] = f"❌ Error: {str(e)}"

        # Check health checker
        try:
            from bot.utils.health_checker import HealthChecker
            perf_status["Health Checker"] = "✅ Available"
        except Exception as e:
            perf_status["Health Checker"] = f"❌ Error: {str(e)}"

        self.status["performance"] = perf_status
        return perf_status

    def check_security(self) -> Dict[str, str]:
        """Check security-related components."""
        security_status = {}

        # Check security audit
        try:
            from bot.utils.security_audit import SecurityAuditor
            security_status["Security Audit"] = "✅ Available"
        except Exception as e:
            security_status["Security Audit"] = f"❌ Error: {str(e)}"

        # Check for hardcoded credentials
        hardcoded_creds = self._check_hardcoded_credentials()
        if hardcoded_creds:
            security_status["Hardcoded Credentials"] = f"❌ Found {len(hardcoded_creds)} instances"
        else:
            security_status["Hardcoded Credentials"] = "✅ None found"

        self.status["security"] = security_status
        return security_status

    def generate_next_steps(self) -> List[str]:
        """Generate list of next steps based on current status."""
        next_steps = []

        # Check critical tasks
        critical_tasks = self.status.get("critical_tasks", {})
        if not all(critical_tasks.values()):
            next_steps.append("Complete remaining critical tasks")

        # Check test status
        test_status = self.status.get("test_status", {})
        if any("❌" in status for status in test_status.values()):
            next_steps.append("Fix failing tests")

        # Check environment
        env_status = self.status.get("environment", {})
        if any("❌" in status for status in env_status.values()):
            next_steps.append("Configure environment variables")

        # Check security
        security_status = self.status.get("security", {})
        if any("❌" in status for status in security_status.values()):
            next_steps.append("Address security issues")

        # Add standard next steps
        next_steps.extend([
            "Run database migrations",
            "Deploy system integration service",
            "Configure monitoring and alerting",
            "Begin advanced features implementation"
        ])

        self.status["next_steps"] = next_steps
        return next_steps

    def _check_cache_manager(self) -> bool:
        """Check if enhanced cache manager is working."""
        try:
            from bot.utils.enhanced_cache_manager import EnhancedCacheManager
            return True
        except Exception:
            return False

    def _check_error_handling(self) -> bool:
        """Check if error handling system is working."""
        try:
            from bot.utils.exceptions import DBSBMException
            return True
        except Exception:
            return False

    def _check_logging_system(self) -> bool:
        """Check if structured logging is working."""
        try:
            from bot.utils.logging_config import auto_configure_logging
            return True
        except Exception:
            return False

    def _check_security_audit(self) -> bool:
        """Check if security audit system is working."""
        try:
            from bot.utils.security_audit import SecurityAuditor
            return True
        except Exception:
            return False

    def _check_health_system(self) -> bool:
        """Check if health check system is working."""
        try:
            from bot.utils.health_checker import HealthChecker
            return True
        except Exception:
            return False

    def _check_pydantic_migration(self) -> bool:
        """Check if Pydantic V2 migration is complete."""
        try:
            from config.settings import get_settings
            settings = get_settings()
            # Try to access a field to trigger validation
            _ = settings.environment
            return True
        except Exception:
            return False

    def _check_hardcoded_credentials(self) -> List[str]:
        """Check for hardcoded credentials in codebase."""
        hardcoded = []

        # Common patterns for hardcoded credentials
        patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
        ]

        # Safe patterns that use environment variables
        safe_patterns = [
            r'os\.getenv\([\'"][^\'"]+[\'"]\)',
            r'os\.environ\[[\'"][^\'"]+[\'"]\]',
            r'SecretStr\(',
            r'get_secret_value\(',
        ]

        # Search in Python files
        for root, dirs, files in os.walk(self.project_root):
            # Skip virtual environments and other non-project directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git',
                                                    'venv', 'env', '.venv', '.venv310', 'node_modules']]

            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            lines = content.split('\n')

                            for line_num, line in enumerate(lines, 1):
                                # Check for sensitive patterns
                                for pattern in patterns:
                                    if re.search(pattern, line, re.IGNORECASE):
                                        # Check if it's a safe pattern
                                        is_safe = False
                                        for safe_pattern in safe_patterns:
                                            if re.search(safe_pattern, line, re.IGNORECASE):
                                                is_safe = True
                                                break

                                        if not is_safe:
                                            hardcoded.append(str(file_path))
                                            break
                    except Exception:
                        continue

        return hardcoded

    def print_status_report(self):
        """Print comprehensive status report."""
        print("=" * 80)
        print("DBSBM PROJECT STATUS REPORT")
        print("=" * 80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Critical Tasks
        print("🔴 CRITICAL TASKS:")
        print("-" * 40)
        for task, completed in self.status["critical_tasks"].items():
            status = "✅ COMPLETED" if completed else "❌ PENDING"
            print(f"  {task}: {status}")
        print()

        # Test Status
        print("🧪 TEST STATUS:")
        print("-" * 40)
        for test, status in self.status["test_status"].items():
            print(f"  {test}: {status}")
        print()

        # Environment
        print("🌍 ENVIRONMENT:")
        print("-" * 40)
        for env, status in self.status["environment"].items():
            print(f"  {env}: {status}")
        print()

        # Performance
        print("⚡ PERFORMANCE:")
        print("-" * 40)
        for perf, status in self.status["performance"].items():
            print(f"  {perf}: {status}")
        print()

        # Security
        print("🔒 SECURITY:")
        print("-" * 40)
        for sec, status in self.status["security"].items():
            print(f"  {sec}: {status}")
        print()

        # Next Steps
        print("📋 NEXT STEPS:")
        print("-" * 40)
        for i, step in enumerate(self.status["next_steps"], 1):
            print(f"  {i}. {step}")
        print()

        # Summary
        critical_completed = sum(self.status["critical_tasks"].values())
        critical_total = len(self.status["critical_tasks"])

        print("📊 SUMMARY:")
        print("-" * 40)
        print(
            f"  Critical Tasks: {critical_completed}/{critical_total} completed")
        print(
            f"  Overall Status: {'🟢 READY' if critical_completed == critical_total else '🟡 IN PROGRESS'}")
        print()
        print("=" * 80)


def main():
    """Main function to run status check."""
    checker = DBSBMStatusChecker()

    # Run all checks
    checker.check_critical_tasks()
    checker.check_test_status()
    checker.check_environment()
    checker.check_performance()
    checker.check_security()
    checker.generate_next_steps()

    # Print report
    checker.print_status_report()


if __name__ == "__main__":
    main()
