import subprocess
import time
import datetime
import pytz
import os
import signal

# Path to your bot's main.py
BOT_PATH = os.path.join(os.path.dirname(__file__), "main.py")
SHUTDOWN_FILE = os.path.join(os.path.dirname(__file__), "shutdown.flag")
RESTART_INTERVAL = 60  # seconds between checks
TIMEZONE = pytz.timezone("US/Eastern")


def is_first_monday(dt):
    # dt is a datetime object in local time
    return dt.weekday() == 0 and 1 <= dt.day <= 7


def next_restart_time(now):
    # Find the next first Monday at 00:00 EST
    year = now.year
    month = now.month
    # Find first Monday of this or next month
    for add_month in range(0, 2):
        m = month + add_month
        if m > 12:
            m -= 12
            year += 1
        for day in range(1, 8):
            dt = datetime.datetime(year, m, day, 0, 0, 0)
            dt = TIMEZONE.localize(dt)
            if dt.weekday() == 0:
                if dt > now:
                    return dt
                break
    # Fallback: next month
    return now + datetime.timedelta(days=30)


def run_bot():
    return subprocess.Popen(["python", BOT_PATH])


def main():
    while True:
        now = datetime.datetime.now(TIMEZONE)
        restart_at = next_restart_time(now)
        print(f"[Service] Next scheduled restart: {restart_at}")
        bot_proc = run_bot()
        while True:
            time.sleep(RESTART_INTERVAL)
            # Manual shutdown
            if os.path.exists(SHUTDOWN_FILE):
                print("[Service] Shutdown flag detected. Stopping bot and exiting.")
                bot_proc.terminate()
                bot_proc.wait()
                os.remove(SHUTDOWN_FILE)
                return
            # Scheduled restart
            now = datetime.datetime.now(TIMEZONE)
            if now >= restart_at:
                print("[Service] Scheduled restart time reached. Restarting bot.")
                bot_proc.terminate()
                bot_proc.wait()
                break  # Restart outer loop


if __name__ == "__main__":
    main()
