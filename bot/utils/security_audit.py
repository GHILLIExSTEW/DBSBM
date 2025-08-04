"""
Security audit utilities for DBSBM system.

This module provides security scanning and audit capabilities
to identify potential security vulnerabilities.
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path


logger = logging.getLogger(__name__)


class SecurityAuditor:
    """Security auditor for scanning code and configuration files."""

    def __init__(self):
        self.security_issues = []
        self.sensitive_patterns = [
            # Password patterns
            r'password\s*=\s*[\'"][^\'"]+[\'"]',
            r'passwd\s*=\s*[\'"][^\'"]+[\'"]',
            r'pwd\s*=\s*[\'"][^\'"]+[\'"]',
            # API key patterns
            r'api_key\s*=\s*[\'"][^\'"]+[\'"]',
            r'apikey\s*=\s*[\'"][^\'"]+[\'"]',
            r'token\s*=\s*[\'"][^\'"]+[\'"]',
            r'secret\s*=\s*[\'"][^\'"]+[\'"]',
            # Database connection patterns
            r'mysql_password\s*=\s*[\'"][^\'"]+[\'"]',
            r'postgres_password\s*=\s*[\'"][^\'"]+[\'"]',
            r'redis_password\s*=\s*[\'"][^\'"]+[\'"]',
            # Discord token patterns
            r'discord_token\s*=\s*[\'"][^\'"]+[\'"]',
            r'bot_token\s*=\s*[\'"][^\'"]+[\'"]',
            # AWS credentials
            r'aws_access_key\s*=\s*[\'"][^\'"]+[\'"]',
            r'aws_secret_key\s*=\s*[\'"][^\'"]+[\'"]',
            # Generic secret patterns
            r'secret_key\s*=\s*[\'"][^\'"]+[\'"]',
            r'private_key\s*=\s*[\'"][^\'"]+[\'"]',
        ]

        self.safe_patterns = [
            # Safe patterns that use environment variables
            r'os\.getenv\([\'"][^\'"]+[\'"]\)',
            r'os\.environ\[[\'"][^\'"]+[\'"]\]',
            r"SecretStr\(",
            r"get_secret_value\(",
        ]

        self.ignored_directories = {
            "__pycache__",
            ".git",
            ".vscode",
            ".idea",
            "node_modules",
            "venv",
            "env",
            ".env",
            "logs",
            "static",
            "templates",
            "migrations",
        }

        self.ignored_files = {
            ".gitignore",
            ".env.example",
            "requirements.txt",
            "README.md",
            "LICENSE",
            "*.log",
            "*.pyc",
        }

    def scan_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Scan a single file for security issues."""
        issues = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

                for line_num, line in enumerate(lines, 1):
                    # Check for sensitive patterns
                    for pattern in self.sensitive_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            # Check if it's a safe pattern
                            is_safe = False
                            for safe_pattern in self.safe_patterns:
                                if re.search(safe_pattern, line, re.IGNORECASE):
                                    is_safe = True
                                    break

                            if not is_safe:
                                issues.append(
                                    {
                                        "file": file_path,
                                        "line": line_num,
                                        "line_content": line.strip(),
                                        "pattern": pattern,
                                        "severity": "HIGH",
                                        "type": "HARDCODED_CREDENTIAL",
                                    }
                                )

                # Check for other security issues
                issues.extend(
                    self._check_additional_security_issues(file_path, content, lines)
                )

        except Exception as e:
            logger.warning(f"Error scanning file {file_path}: {e}")

        return issues

    def _check_additional_security_issues(
        self, file_path: str, content: str, lines: List[str]
    ) -> List[Dict[str, Any]]:
        """Check for additional security issues beyond hardcoded credentials."""
        issues = []

        # Check for debug statements in production code
        if "logger.debug" in content and "test" not in file_path.lower():
            debug_lines = []
            for line_num, line in enumerate(lines, 1):
                if "logger.debug" in line:
                    debug_lines.append(line_num)

            if debug_lines:
                issues.append(
                    {
                        "file": file_path,
                        "lines": debug_lines,
                        "severity": "MEDIUM",
                        "type": "DEBUG_LOGGING",
                        "description": "Debug logging found in production code",
                    }
                )

        # Check for SQL injection vulnerabilities
        sql_patterns = [
            r'execute\([\'"][^\'"]*%s[^\'"]*[\'"]',
            r'execute\([\'"][^\'"]*\{[^\'"]*\}[\'"]',
            r'execute\([\'"][^\'"]*\+[^\'"]*[\'"]',
        ]

        for pattern in sql_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(
                    {
                        "file": file_path,
                        "severity": "HIGH",
                        "type": "SQL_INJECTION",
                        "description": "Potential SQL injection vulnerability",
                    }
                )
                break

        # Check for eval() usage
        if "eval(" in content:
            issues.append(
                {
                    "file": file_path,
                    "severity": "CRITICAL",
                    "type": "EVAL_USAGE",
                    "description": "eval() function usage detected",
                }
            )

        # Check for exec() usage
        if "exec(" in content:
            issues.append(
                {
                    "file": file_path,
                    "severity": "CRITICAL",
                    "type": "EXEC_USAGE",
                    "description": "exec() function usage detected",
                }
            )

        return issues

    def scan_directory(self, directory: str) -> List[Dict[str, Any]]:
        """Scan a directory for security issues."""
        all_issues = []

        for root, dirs, files in os.walk(directory):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignored_directories]

            for file in files:
                file_path = os.path.join(root, file)

                # Skip ignored files
                if any(file.endswith(ext) for ext in [".pyc", ".log", ".tmp"]):
                    continue

                # Only scan Python files and configuration files
                if file.endswith((".py", ".yaml", ".yml", ".json", ".ini", ".cfg")):
                    issues = self.scan_file(file_path)
                    all_issues.extend(issues)

        return all_issues

    def generate_report(self, issues: List[Dict[str, Any]]) -> str:
        """Generate a security audit report."""
        if not issues:
            return "✅ No security issues found!"

        report = "🔒 Security Audit Report\n"
        report += "=" * 50 + "\n\n"

        # Group issues by severity
        by_severity = {}
        for issue in issues:
            severity = issue.get("severity", "UNKNOWN")
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(issue)

        # Report by severity
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            if severity in by_severity:
                report += f"\n{severity} Issues ({len(by_severity[severity])}):\n"
                report += "-" * 30 + "\n"

                for issue in by_severity[severity]:
                    report += (
                        f"• {issue['type']}: {issue.get('file', 'Unknown file')}\n"
                    )
                    if "line" in issue:
                        report += (
                            f"  Line {issue['line']}: {issue.get('line_content', '')}\n"
                        )
                    if "description" in issue:
                        report += f"  Description: {issue['description']}\n"
                    report += "\n"

        # Summary
        total_issues = len(issues)
        critical_count = len(by_severity.get("CRITICAL", []))
        high_count = len(by_severity.get("HIGH", []))
        medium_count = len(by_severity.get("MEDIUM", []))
        low_count = len(by_severity.get("LOW", []))

        report += f"\nSummary:\n"
        report += f"Total Issues: {total_issues}\n"
        report += f"Critical: {critical_count}\n"
        report += f"High: {high_count}\n"
        report += f"Medium: {medium_count}\n"
        report += f"Low: {low_count}\n"

        return report

    def fix_issues(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate fix suggestions for security issues."""
        fixes = []

        for issue in issues:
            if issue["type"] == "HARDCODED_CREDENTIAL":
                fixes.append(
                    f"Replace hardcoded credential in {issue['file']} line {issue['line']} with environment variable"
                )

            elif issue["type"] == "DEBUG_LOGGING":
                fixes.append(
                    f"Remove or change debug logging in {issue['file']} to INFO level for production"
                )

            elif issue["type"] == "SQL_INJECTION":
                fixes.append(
                    f"Use parameterized queries in {issue['file']} to prevent SQL injection"
                )

            elif issue["type"] in ["EVAL_USAGE", "EXEC_USAGE"]:
                fixes.append(
                    f"Replace {issue['type'].lower()} with safer alternatives in {issue['file']}"
                )

        return fixes


def run_security_audit(directory: str = ".") -> str:
    """Run a comprehensive security audit."""
    auditor = SecurityAuditor()
    issues = auditor.scan_directory(directory)
    report = auditor.generate_report(issues)
    return report


def check_environment_security() -> Dict[str, Any]:
    """Check environment variables for security issues."""
    security_check = {"missing_vars": [], "weak_vars": [], "recommendations": []}

    # Required environment variables
    required_vars = ["DISCORD_TOKEN", "MYSQL_PASSWORD", "REDIS_PASSWORD", "DBSBM_ENV"]

    # Check for missing variables
    for var in required_vars:
        if not os.getenv(var):
            security_check["missing_vars"].append(var)

    # Check for weak passwords
    password_vars = ["MYSQL_PASSWORD", "REDIS_PASSWORD"]
    for var in password_vars:
        value = os.getenv(var)
        if value and len(value) < 8:
            security_check["weak_vars"].append(var)

    # Generate recommendations
    if security_check["missing_vars"]:
        security_check["recommendations"].append(
            f"Set missing environment variables: {', '.join(security_check['missing_vars'])}"
        )

    if security_check["weak_vars"]:
        security_check["recommendations"].append(
            f"Strengthen weak passwords: {', '.join(security_check['weak_vars'])}"
        )

    return security_check


# Command line interface
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = "."

    print("Running security audit...")
    report = run_security_audit(directory)
    print(report)

    print("\nChecking environment security...")
    env_check = check_environment_security()
    if env_check["missing_vars"] or env_check["weak_vars"]:
        print("Environment security issues found:")
        for issue in env_check["recommendations"]:
            print(f"• {issue}")
    else:
        print("✅ Environment security check passed!")
