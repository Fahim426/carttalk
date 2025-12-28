import os
import shutil
import sys
import subprocess
import site

def repair():
    print("Detected Python executable:", sys.executable)
    
    # Get site-packages
    site_packages = site.getsitepackages()
    print("Site packages dirs:", site_packages)
    
    libs_to_fix = ["httpcore", "httpx", "google_genai", "google"]
    
    for sp in site_packages:
        for lib in libs_to_fix:
            lib_path = os.path.join(sp, lib)
            if os.path.exists(lib_path):
                print(f"Removing corrupted library: {lib_path}")
                try:
                    shutil.rmtree(lib_path)
                    print("  -> Success")
                except Exception as e:
                    print(f"  -> Failed: {e}")

    print("\nRe-installing clean versions (ignoring cache)...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "google-genai", "httpx", "httpcore", 
            "--force-reinstall", "--no-cache-dir", "--upgrade"
        ])
        print("\nSUCCESS! Libraries repaired.")
    except subprocess.CalledProcessError as e:
        print(f"\nFAILED to reinstall: {e}")

if __name__ == "__main__":
    repair()
