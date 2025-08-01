#!/usr/bin/env python3
"""
Startup script for DBSBM services.
Starts the fetcher and webapp with proper error handling.
"""

import os
import sys
import subprocess
import time
import signal
import tempfile
from pathlib import Path
from datetime import datetime

def check_port_available(port):
    """Check if a port is available."""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False

def cleanup_stale_processes():
    """Clean up any stale processes or lock files."""
    print("🧹 Cleaning up stale processes...")
    
    # Clean up fetcher lock file
    lock_file = Path(tempfile.gettempdir()) / "dbsbm_fetcher.lock"
    if lock_file.exists():
        try:
            lock_age = datetime.now() - datetime.fromtimestamp(lock_file.stat().st_mtime)
            if lock_age.total_seconds() > 600:  # 10 minutes
                print(f"🗑️  Removing stale fetcher lock file")
                lock_file.unlink()
        except Exception as e:
            print(f"⚠️  Error cleaning lock file: {e}")
    
    # Kill any existing Python processes that might be our services
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'python.exe':
                    cmdline = proc.info['cmdline']
                    if cmdline and any('fetcher' in arg.lower() or 'webapp' in arg.lower() for arg in cmdline):
                        print(f"🔄 Terminating existing process: PID {proc.pid}")
                        proc.terminate()
                        proc.wait(timeout=5)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                continue
    except ImportError:
        print("⚠️  psutil not available - cannot check for processes")

def start_fetcher():
    """Start the fetcher process."""
    print("🚀 Starting fetcher...")
    
    fetcher_script = "bot/utils/comprehensive_fetcher.py"
    if not os.path.exists(fetcher_script):
        print(f"❌ Comprehensive fetcher script not found: {fetcher_script}")
        return None
    
    try:
        process = subprocess.Popen(
            [sys.executable, fetcher_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"✅ Comprehensive fetcher started with PID: {process.pid}")
        return process
    except Exception as e:
        print(f"❌ Failed to start fetcher: {e}")
        return None

def start_webapp():
    """Start the webapp process."""
    print("🌐 Starting webapp...")
    
    # Check if port 25594 is available
    if not check_port_available(25594):
        print("⚠️  Port 25594 is already in use")
        return None
    
    webapp_script = "bot/main.py"  # Assuming this is the webapp entry point
    if not os.path.exists(webapp_script):
        print(f"❌ Webapp script not found: {webapp_script}")
        return None
    
    try:
        process = subprocess.Popen(
            [sys.executable, webapp_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"✅ Webapp started with PID: {process.pid}")
        return process
    except Exception as e:
        print(f"❌ Failed to start webapp: {e}")
        return None

def monitor_processes(fetcher_process, webapp_process):
    """Monitor the running processes."""
    print("👀 Monitoring processes...")
    
    try:
        while True:
            # Check if processes are still running
            if fetcher_process and fetcher_process.poll() is not None:
                print("⚠️  Fetcher process stopped unexpectedly")
                fetcher_process = start_fetcher()
            
            if webapp_process and webapp_process.poll() is not None:
                print("⚠️  Webapp process stopped unexpectedly")
                webapp_process = start_webapp()
            
            time.sleep(30)  # Check every 30 seconds
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        
        # Terminate processes gracefully
        if fetcher_process:
            fetcher_process.terminate()
            try:
                fetcher_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                fetcher_process.kill()
        
        if webapp_process:
            webapp_process.terminate()
            try:
                webapp_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                webapp_process.kill()
        
        print("✅ Services stopped")

def main():
    """Main startup function."""
    print("🎯 DBSBM Service Startup")
    print("=" * 40)
    
    # Clean up any stale processes
    cleanup_stale_processes()
    
    # Start services
    fetcher_process = start_fetcher()
    time.sleep(2)  # Give fetcher time to start
    
    webapp_process = start_webapp()
    time.sleep(2)  # Give webapp time to start
    
    if not fetcher_process and not webapp_process:
        print("❌ Failed to start any services")
        sys.exit(1)
    
    print("\n✅ Services started successfully!")
    print("📊 Fetcher: Processing sports data")
    print("🌐 Webapp: Available at http://localhost:25594")
    print("\nPress Ctrl+C to stop all services")
    
    # Monitor processes
    monitor_processes(fetcher_process, webapp_process)

if __name__ == "__main__":
    main() 