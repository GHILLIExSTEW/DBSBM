#!/usr/bin/env python3
"""
Script to identify long functions (over 100 lines) for refactoring.
This helps with Task 4.4: Refactor long functions.
"""

import os
import ast
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LongFunctionFinder:
    """Find functions that are over 100 lines long."""

    def __init__(self, max_lines: int = 100):
        self.max_lines = max_lines
        self.long_functions = []

    def analyze_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze a single Python file for long functions."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            functions = []

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Calculate function length
                    start_line = node.lineno
                    end_line = node.end_lineno if hasattr(
                        node, 'end_lineno') else start_line

                    # Count actual lines in function
                    lines = content.split('\n')
                    function_lines = lines[start_line-1:end_line]
                    actual_lines = len(
                        [line for line in function_lines if line.strip()])

                    if actual_lines > self.max_lines:
                        functions.append({
                            'name': node.name,
                            'start_line': start_line,
                            'end_line': end_line,
                            'lines': actual_lines,
                            'file': file_path,
                            'is_async': isinstance(node, ast.AsyncFunctionDef)
                        })

            return functions

        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return []

    def analyze_directory(self, directory: str) -> List[Dict[str, Any]]:
        """Analyze all Python files in a directory recursively."""
        all_functions = []

        for root, dirs, files in os.walk(directory):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in [
                '.git', '__pycache__', '.pytest_cache', '.venv', 'venv']]

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    functions = self.analyze_file(file_path)
                    all_functions.extend(functions)

        return all_functions

    def generate_report(self, functions: List[Dict[str, Any]]) -> str:
        """Generate a formatted report of long functions."""
        if not functions:
            return "No functions over 100 lines found."

        # Sort by line count (descending)
        functions.sort(key=lambda x: x['lines'], reverse=True)

        report = f"Found {len(functions)} functions over {self.max_lines} lines:\n\n"

        for func in functions:
            report += f"📁 {func['file']}\n"
            report += f"   Function: {func['name']} ({'async ' if func['is_async'] else ''}def)\n"
            report += f"   Lines: {func['lines']} (lines {func['start_line']}-{func['end_line']})\n"
            report += f"   Priority: {'🔴 HIGH' if func['lines'] > 200 else '🟡 MEDIUM' if func['lines'] > 150 else '🟢 LOW'}\n"
            report += "\n"

        return report


def main():
    """Main function to run the analysis."""
    finder = LongFunctionFinder(max_lines=100)

    # Analyze the bot directory
    bot_dir = "bot"
    if os.path.exists(bot_dir):
        logger.info(f"Analyzing {bot_dir} directory...")
        functions = finder.analyze_directory(bot_dir)

        # Generate and print report
        report = finder.generate_report(functions)
        print(report)

        # Save report to file
        with open("long_functions_report.txt", "w", encoding="utf-8") as f:
            f.write(report)

        logger.info(f"Report saved to long_functions_report.txt")
        logger.info(f"Found {len(functions)} functions over 100 lines")

        # Summary by priority
        high_priority = [f for f in functions if f['lines'] > 200]
        medium_priority = [f for f in functions if 150 < f['lines'] <= 200]
        low_priority = [f for f in functions if 100 < f['lines'] <= 150]

        print(f"\n📊 Summary:")
        print(f"🔴 High Priority (>200 lines): {len(high_priority)}")
        print(f"🟡 Medium Priority (150-200 lines): {len(medium_priority)}")
        print(f"🟢 Low Priority (100-150 lines): {len(low_priority)}")

    else:
        logger.error(f"Directory {bot_dir} not found")


if __name__ == "__main__":
    main()
