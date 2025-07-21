import os
import re
import subprocess
import time
from fastapi import APIRouter, Form, HTTPException

router = APIRouter()

# Define the path for the persistent audit rules file.
AUDIT_RULES_FILE = "/etc/audit/rules.d/99-tiersense.rules"

@router.post("/configure-monitoring")
async def configure_monitoring(target_dir: str = Form(...)):
    """
    Configures and applies a persistent auditd rule to monitor a specific directory
    for file access.
    """
    try:
        # --- Step 1: Sanitize and Validate User Input ---
        target_dir = target_dir.strip()

        # Security: Sanitize the input to allow only valid path characters.
        if not re.match(r'^(/host-root|/mnt/nfs)/[a-zA-Z0-9/._-]+$', target_dir):
            raise HTTPException(
                status_code=400,
                detail="Invalid characters in path. Only letters, numbers, and /._- are allowed."
            )

        # Validate that the path uses one of the allowed, mounted prefixes.
        if not (target_dir.startswith("/host-root/") or target_dir.startswith("/mnt/nfs/")):
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
        
        # Translate the container path to the actual path on the host machine.
        host_path = target_dir.replace("/host-root", "", 1)
        print(f"[INFO] Configuring persistent monitoring for host path: {host_path}")

        # --- THIS IS THE FIX ---
        # The rule now correctly uses the `host_path` variable.
        # The key is also updated to match the parser.
        rule_key = "tiersense_monitoring"
        rule = f"-w {host_path} -p rwxa -k {rule_key}"

        # Write the rule to the persistent audit rules file.
        with open(AUDIT_RULES_FILE, "w") as f:
            f.write(f"# TierSense monitoring rule generated on {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-D\n") # Clear all previous rules first
            f.write(rule + "\n")

        # Load the rules from the file immediately to activate monitoring.
        subprocess.run(
            ["auditctl", "-R", AUDIT_RULES_FILE],
            check=True, capture_output=True, text=True
        )

        return {"status": "success", "message": f"Monitoring successfully configured for: {host_path}"}

    except subprocess.CalledProcessError as e:
        error_details = e.stderr.strip() if e.stderr else "Unknown error from auditctl."
        print(f"[ERROR] auditctl command failed: {error_details}")
        raise HTTPException(status_code=500, detail=f"Failed to apply audit rule: {error_details}")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
