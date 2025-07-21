import os
import subprocess
from fastapi import APIRouter, Form, HTTPException

router = APIRouter()

@router.post("/configure-monitoring")
async def configure_monitoring(target_dir: str = Form(...)):
    """Sets an auditd rule on the host to monitor the specified directory."""
    target_dir = target_dir.strip()

    # The path provided by the user (e.g., /host-root/home/user) is the path *inside the container*.
    # We must translate this to the actual path on the host for the auditd rule by removing the prefix.
    host_path = target_dir.replace("/host-root", "", 1)

    # Reliability Check: Verify the path exists inside the container before proceeding.
    if not os.path.exists(target_dir):
        raise HTTPException(status_code=404, detail=f"Path not found inside container: '{target_dir}'. Please ensure the path is correct and accessible.")

    try:
        # Define the unique key that the parser will look for.
        rule_key = "tiersense_monitoring"
        
        # Clear all previous audit rules to ensure a clean state for the new analysis.
        subprocess.run(["auditctl", "-D"], check=True, capture_output=True)
        
        # Add the new rule with the correct key to watch the specified host path for read, write, execute, and attribute changes.
        rule = f"-w {host_path} -p rwxa -k {rule_key}"
        subprocess.run(["auditctl"] + rule.split(), check=True, capture_output=True, text=True)
        
        return {"status": "success", "message": f"Monitoring configured for host path: {host_path}"}
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode().strip() if e.stderr else "Unknown error from auditctl."
        raise HTTPException(status_code=500, detail=f"Failed to apply audit rule: {error_message}")
