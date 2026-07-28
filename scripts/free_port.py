# scripts/free_port.py
import sys
import subprocess

def main():
    cmd = [sys.executable, "scripts/ensure_single_instance.py"]
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
