"""
PureClip Build Automation
Compiles PureClip into a standalone Windows .exe application.
"""

import os
import sys
import subprocess


def build_exe():
    print("✦ Building PureClip standalone Windows executable...")
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name=PureClip",
        "--onefile",
        "--noconsole",
        "--clean",
        "--add-data=src;src",
        "src/main.py"
    ]
    
    result = subprocess.run(cmd)
    if result.returncode == 0:
        exe_path = os.path.abspath("dist/PureClip.exe")
        print("\n==========================================")
        print("✓ Build Successful!")
        print(f"Standalone Windows App created at:\n{exe_path}")
        print("==========================================")
    else:
        print("\n❌ Build failed with return code:", result.returncode)


if __name__ == "__main__":
    build_exe()
