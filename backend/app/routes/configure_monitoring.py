# app/routes/configure_monitoring.py

import os
import re
import subprocess
import time
from fastapi import APIRouter, Form, HTTPException

router = APIRouter()

# Define the path for the persistent audit rules file.
# This ensures monitoring rules survive a system reboot.
AUDIT_RULES_FILE = "/etc/audit/rules.d/99-tiersense.rules"

@router.post("/configure-monitoring")
async def configure_monitoring(target_dir: str = Form(...)):
    """
    Configures and applies a persistent auditd rule to monitor a specific directory
    for file access, then ensures the Filebeat service is running to collect the logs.
    """
    try:
        # --- Step 1: Sanitize and Validate User Input ---
        target_dir = target_dir.strip()

        # Security: Sanitize the input to allow only valid path characters.
        # This prevents potential command injection vulnerabilities.
        if not re.match(r'^(/host-root|/mnt/nfs)/[a-zA-Z0-9/._-]+$', target_dir):
            raise HTTPException(
                status_code=400,
                detail="Invalid characters in path. Only letters, numbers, and /._- are allowed."
            )

        # Validate that the path uses one of the allowed, mounted prefixes.
        is_host_path = target_dir.startswith("/host-root/")
        is_nfs_path = target_dir.startswith("/mnt/nfs/")
        if not (is_host_path or is_nfs_path):
            raise HTTPException(
                status_code=400,
                detail="Invalid path prefix. Must start with /host-root/ or /mnt/nfs/."
            )

        # Reliability: Check if the directory actually exists inside the container.
        if not os.path.exists(target_dir):
            raise HTTPException(
                status_code=404,
                detail=f"Path not found inside container: '{target_dir}'. Ensure it is mounted correctly."
            )

        # --- Step 2: Create and Apply Persistent Audit Rule ---
        print(f"[INFO] Configuring persistent monitoring for: {target_dir}")
        rule = f"-w {target_dir} -p rwxa -k tiering_monitor"

        # Write the rule to the persistent audit rules file.
        # This ensures the rule is re-applied automatically on system startup.
        with open(AUDIT_RULES_FILE, "w") as f:
            f.write(f"# TierSense monitoring rule generated on {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-D\n") # Clear previous rules first
            f.write(rule + "\n")

        # Load the rules from the file immediately to activate monitoring.
        # The '-R' flag reads all rules from the specified file.
        subprocess.run(
            ["auditctl", "-R", AUDIT_RULES_FILE],
            check=True, capture_output=True, text=True
        )

        # --- Step 3: Reliably Restart Filebeat Service ---
        print("[INFO] Restarting Filebeat service to apply configuration...")
        
        # Terminate any existing Filebeat process.
        subprocess.run(["pkill", "-f", "filebeat"], check=False)

        # Brief pause to ensure the old process has time to shut down.
        time.sleep(1)

        # Start a new Filebeat instance in the background.
        # Explicitly provide the config file path for clarity.
        subprocess.Popen(["filebeat", "-e", "-c", "/etc/filebeat/filebeat.yml"])

        return {"status": "success", "message": f"Monitoring successfully configured for: {target_dir}"}

    except subprocess.CalledProcessError as e:
        # Provide specific feedback if the 'auditctl' command fails.
        error_details = e.stderr or e.stdout or "No output from command."
        print(f"[ERROR] auditctl command failed: {error_details.strip()}")
        raise HTTPException(status_code=500, detail=f"Failed to apply audit rule: {error_details.strip()}")
    except Exception as e:
        # Catch-all for any other unexpected errors during the process.
        print(f"[ERROR] An unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")