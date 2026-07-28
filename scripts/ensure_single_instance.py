# scripts/ensure_single_instance.py
import subprocess
import os
import sys

def main():
    print("[ENSURE-SINGLE-INSTANCE] Starting port and process cleanup for app.py...")
    
    current_pid = os.getpid()
    
    # 1. Kill any process containing "app.py" in command line (except ourselves)
    try:
        powershell_cmd = (
            f'powershell -Command "Get-CimInstance Win32_Process -Filter \\"CommandLine like \'%app.py%\'\\" | '
            f'Where-Object {{ $_.ProcessId -ne {current_pid} }} | '
            f'ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force }}"'
        )
        subprocess.run(powershell_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[ENSURE-SINGLE-INSTANCE] Error killing app.py processes: {e}")

    # 2. Kill any process listening on port 8000 (and its children tree)
    try:
        output = subprocess.check_output("netstat -ano", shell=True).decode('utf-8')
        pids = set()
        for line in output.splitlines():
            if ":8000" in line and "LISTENING" in line:
                parts = line.strip().split()
                if len(parts) >= 5:
                    pids.add(parts[-1])
        for pid_str in pids:
            try:
                pid = int(pid_str)
                if pid != current_pid:
                    print(f"[ENSURE-SINGLE-INSTANCE] Terminating process tree {pid} listening on port 8000...")
                    subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                continue
    except Exception as e:
        print(f"[ENSURE-SINGLE-INSTANCE] Error checking port 8000: {e}")

if __name__ == "__main__":
    main()
