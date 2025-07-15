import csv
import os

backup_file = os.path.join("..", "data", "players.csv.backup.20250715_161359")
main_file = os.path.join("..", "data", "players.csv")

print("Backup file headers:")
with open(backup_file, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    headers = next(reader)
    for i, h in enumerate(headers):
        print(f"{i+1:2d}. {h}")

print("\nMain file headers:")
with open(main_file, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    headers = next(reader)
    for i, h in enumerate(headers):
        print(f"{i+1:2d}. {h}")
