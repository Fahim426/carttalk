import os
import shutil
from pathlib import Path

# Target directories to clean
targets = [
    r"C:\Users\fahim\AppData\Local\Programs\Python\Python311\Lib\site-packages\httpcore",
    r"C:\Users\fahim\AppData\Local\Programs\Python\Python311\Lib\site-packages\httpx",
    r"D:\project\carttalk\backend"
]

print("Starting deep clean of __pycache__...")

for target in targets:
    p = Path(target)
    if not p.exists():
        print(f"Path not found: {p}")
        continue
        
    # Walk and remove __pycache__
    for root, dirs, files in os.walk(p):
        for d in dirs:
            if d == "__pycache__":
                full_path = os.path.join(root, d)
                try:
                    shutil.rmtree(full_path)
                    print(f"Deleted: {full_path}")
                except Exception as e:
                    print(f"Failed to delete {full_path}: {e}")
        
        # Also remove .pyc files that might be loose (rare but possible)
        for f in files:
            if f.endswith(".pyc"):
                full_path = os.path.join(root, f)
                try:
                    os.remove(full_path)
                    print(f"Deleted file: {full_path}")
                except Exception as e:
                    print(f"Failed to delete {full_path}: {e}")

print("Clean complete.")
