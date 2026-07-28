# scripts/free_port.py
import sys
import subprocess

def main():
    # Forward the execution directly to ensure_single_instance.py
    cmd = [sys.executable, "scripts/ensure_single_instance.py"] + sys.argv[1:]
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
