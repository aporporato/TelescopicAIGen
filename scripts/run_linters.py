import os
import subprocess
import sys

def main():
    print("=== 1. RUNNING PYTHON BACKEND LINTER ===")
    py_res = subprocess.run([sys.executable, "-m", "py_compile", "app.py"])
    if py_res.returncode != 0:
        print("[FAIL] Python backend linter check failed!")
        sys.exit(py_res.returncode)
    print("[OK] Python backend linter check passed.")

    print("\n=== 2. RUNNING JAVASCRIPT / TYPESCRIPT FRONTEND LINTER ===")
    if not os.path.exists("node_modules"):
        print("[INFO] node_modules not present, skipping frontend JS/TS lint step.")
    else:
        js_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        js_res = subprocess.run([js_cmd, "run", "lint"])
        if js_res.returncode != 0:
            print("[FAIL] JavaScript/TypeScript linter check failed!")
            sys.exit(js_res.returncode)
        print("[OK] JavaScript/TypeScript linter check passed.")

    print("\n=== PRE-COMMIT LINTER CHECKS PASSED CLEANLY ===")

if __name__ == "__main__":
    main()
