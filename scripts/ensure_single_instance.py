# scripts/ensure_single_instance.py
import subprocess
import os
import sys
import json

def main():
    # Write a debug log of environment and arguments to see what is passed to the hook
    try:
        with open("scripts/ensure_single_instance_debug.txt", "a") as f:
            f.write(f"=== Hook Triggered ===\n")
            f.write(f"Args: {sys.argv}\n")
            f.write(f"ANTIGRAVITY_SOURCE_METADATA: {os.getenv('ANTIGRAVITY_SOURCE_METADATA')}\n")
    except Exception:
        pass

    # 1. Check if we are running inside Antigravity and get the command being executed
    metadata_str = os.getenv("ANTIGRAVITY_SOURCE_METADATA")
    is_app_start = False
    
    if metadata_str:
        try:
            metadata = json.loads(metadata_str)
            tool_args = metadata.get("tool", {}).get("args", {})
            command_line = tool_args.get("CommandLine", "")
            if "app.py" in command_line:
                is_app_start = True
        except Exception:
            pass
            
    # 2. Fallback to CLI arguments (for Cursor, Codex, Claude Code)
    if not is_app_start and len(sys.argv) > 1:
        command_str = " ".join(sys.argv[1:])
        if "app.py" in command_str:
            is_app_start = True

    # If it's not a command starting app.py, exit early to preserve running instance
    if not is_app_start:
        return

    print("[ENSURE-SINGLE-INSTANCE] Starting port and process cleanup for app.py...")
    
    # 1. Kill any process containing "app.py" in command line (except ourselves)
    try:
        current_pid = os.getpid()
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
                    # Kill using taskkill with /T (tree kill)
                    subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                continue
    except Exception as e:
        print(f"[ENSURE-SINGLE-INSTANCE] Error checking port 8000: {e}")

if __name__ == "__main__":
    main()
