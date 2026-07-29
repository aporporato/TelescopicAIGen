# scripts/ensure_single_instance.py
import subprocess
import os
import sys
import time

def main():
    print("[ENSURE-SINGLE-INSTANCE] Starting port and process cleanup for app.py...")
    
    current_pid = os.getpid()
    
    # 1. Kill any process whose command line contains app.py or uvicorn
    for pattern in ["app.py", "uvicorn"]:
        try:
            ps_script = (
                f"Get-CimInstance Win32_Process | "
                f"Where-Object {{ ($_.CommandLine -like '*{pattern}*') -and $_.ProcessId -ne {current_pid} }} | "
                f"ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }}"
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script])
        except Exception as e:
            print(f"[ENSURE-SINGLE-INSTANCE] Error killing {pattern} processes: {e}")

    # 2. Kill all processes and child trees associated with port 8000
    for attempt in range(5):
        try:
            ps_port_script = (
                f"$tcp = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue; "
                f"if ($tcp) {{ "
                f"  $pids = $tcp | Select-Object -ExpandProperty OwningProcess -Unique; "
                f"  foreach ($p in $pids) {{ "
                f"    if ($p -and $p -ne {current_pid}) {{ "
                f"      Get-CimInstance Win32_Process | Where-Object {{ $_.ParentProcessId -eq $p -or $_.ProcessId -eq $p }} | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }}; "
                f"    }} "
                f"  }} "
                f"}}"
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_port_script])
        except Exception as e:
            print(f"[ENSURE-SINGLE-INSTANCE] Error checking port 8000: {e}")

        # Check if port 8000 is free
        try:
            output = subprocess.check_output(["netstat", "-ano"], stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
            has_8000 = any(":8000" in line and "LISTENING" in line for line in output.splitlines())
            if not has_8000:
                print("[ENSURE-SINGLE-INSTANCE] Port 8000 successfully freed.")
                break
        except Exception:
            pass

        time.sleep(0.3)

if __name__ == "__main__":
    main()




