"""
Fetcher Logging Utility

This module provides daily log rotation for the fetcher with 3-day retention.
Logs are rotated at 00:00 EST each day and old logs are deleted after 3 days.
"""

import logging
import os
import glob
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo
import shutil

# Timezone constants
EST = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")

class FetcherLogger:
    """Custom logger for fetcher with daily rotation and 3-day retention."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.current_log_file = None
        self.logger = None
        self.handler = None
        
        os.makedirs(self.log_dir, exist_ok=True)
        self._setup_logger()
        
    def _setup_logger(self):
        self.logger = logging.getLogger("fetcher")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()
        self.current_log_file = self._get_current_log_file()
        self.handler = logging.FileHandler(self.current_log_file, mode='a', encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.handler.setFormatter(formatter)
        self.logger.addHandler(self.handler)
        self.logger.info("Fetcher logger initialized")
        
    def _get_current_log_file(self) -> str:
        now_est = datetime.now(EST)
        date_str = now_est.strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"fetcher_{date_str}.log")
    
    def _should_rotate_log(self) -> bool:
        now_est = datetime.now(EST)
        current_log_file = self._get_current_log_file()
        return self.current_log_file != current_log_file
    
    def _rotate_log(self):
        if self._should_rotate_log():
            if self.handler:
                self.logger.removeHandler(self.handler)
                self.handler.close()
            self._setup_logger()
            self._cleanup_old_logs()
    
    def _cleanup_old_logs(self):
        try:
            now_est = datetime.now(EST)
            cutoff_date = now_est - timedelta(days=3)
            log_pattern = os.path.join(self.log_dir, "fetcher_*.log")
            log_files = glob.glob(log_pattern)
            for log_file in log_files:
                try:
                    filename = os.path.basename(log_file)
                    date_str = filename.replace("fetcher_", "").replace(".log", "")
                    file_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=EST)
                    if file_date < cutoff_date:
                        os.remove(log_file)
                        print(f"Deleted old log file: {log_file}")
                except Exception as e:
                    print(f"Error processing log file {log_file}: {e}")
        except Exception as e:
            print(f"Error during log cleanup: {e}")
    
    def _ensure_logger_current(self):
        self._rotate_log()
    
    def debug(self, message: str):
        self._ensure_logger_current()
        self.logger.debug(message)
    
    def info(self, message: str):
        self._ensure_logger_current()
        self.logger.info(message)
    
    def warning(self, message: str):
        self._ensure_logger_current()
        self.logger.warning(message)
    
    def error(self, message: str):
        self._ensure_logger_current()
        self.logger.error(message)
    
    def critical(self, message: str):
        self._ensure_logger_current()
        self.logger.critical(message)
    
    def exception(self, message: str):
        self._ensure_logger_current()
        self.logger.exception(message)
    
    def get_current_log_path(self) -> str:
        return self.current_log_file
    
    def get_log_directory(self) -> str:
        return self.log_dir

# Global fetcher logger instance
fetcher_logger = FetcherLogger()

def get_fetcher_logger() -> FetcherLogger:
    return fetcher_logger

def send_error_blip_to_main_log(error_message: str, context: Optional[str] = None):
    """
    Send a simple error blip notification to the main log.
    This provides a quick notification that an error occurred in the fetcher.
    """
    try:
        # Get the main logger (not the fetcher logger)
        main_logger = logging.getLogger("bot.main")
        if not main_logger.handlers:
            # If no handlers, use the root logger
            main_logger = logging.getLogger()
        
        # Create a simple blip message
        blip_message = f"🚨 FETCHER ERROR: {error_message}"
        if context:
            blip_message += f" (Context: {context})"
        blip_message += " - Check fetcher log for details"
        
        # Log as error to make it visible
        main_logger.error(blip_message)
        
    except Exception as e:
        # Fallback to print if logging fails
        print(f"FETCHER ERROR BLIP FAILED: {e}")
        print(f"Original error: {error_message}")

def log_fetcher_operation(operation: str, details: Optional[dict] = None):
    """Log a fetcher operation with optional details."""
    message = f"Operation: {operation}"
    if details:
        message += f" | Details: {details}"
    fetcher_logger.info(message)

def log_fetcher_error(error: str, context: Optional[str] = None):
    """Log a fetcher error and send a blip to the main log."""
    # Log to fetcher log
    message = f"Error: {error}"
    if context:
        message += f" | Context: {context}"
    fetcher_logger.error(message)
    
    # Send blip to main log
    send_error_blip_to_main_log(error, context)

def log_fetcher_statistics(stats: dict):
    """Log fetcher statistics."""
    message = f"Statistics: {stats}"
    fetcher_logger.info(message)

def log_fetcher_startup():
    """Log fetcher startup."""
    fetcher_logger.info("Fetcher startup initiated")

def log_fetcher_shutdown():
    """Log fetcher shutdown."""
    fetcher_logger.info("Fetcher shutdown initiated")

def log_league_fetch(sport: str, league_name: str, success: bool, games_count: int = 0, error: Optional[str] = None):
    """Log league fetch results."""
    status = "SUCCESS" if success else "FAILED"
    message = f"League fetch {status}: {sport} - {league_name}"
    if success:
        message += f" | Games: {games_count}"
    if error:
        message += f" | Error: {error}"
    fetcher_logger.info(message)

def log_api_request(endpoint: str, success: bool, response_time: float = 0.0, error: Optional[str] = None):
    """Log API request results."""
    status = "SUCCESS" if success else "FAILED"
    message = f"API request {status}: {endpoint} | Time: {response_time:.2f}s"
    if error:
        message += f" | Error: {error}"
    fetcher_logger.info(message)

def log_database_operation(operation: str, success: bool, affected_rows: int = 0, error: Optional[str] = None):
    """Log database operation results."""
    status = "SUCCESS" if success else "FAILED"
    message = f"Database {status}: {operation}"
    if success and affected_rows > 0:
        message += f" | Rows: {affected_rows}"
    if error:
        message += f" | Error: {error}"
    fetcher_logger.info(message)

def log_memory_usage(memory_mb: float, cpu_percent: float):
    """Log memory and CPU usage."""
    message = f"System usage: Memory: {memory_mb:.1f}MB | CPU: {cpu_percent:.1f}%"
    fetcher_logger.info(message)

def log_cleanup_operation(operation: str, items_removed: int = 0):
    """Log cleanup operation results."""
    message = f"Cleanup: {operation}"
    if items_removed > 0:
        message += f" | Items removed: {items_removed}"
    fetcher_logger.info(message) 