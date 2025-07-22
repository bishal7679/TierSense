import os
import subprocess
from fastapi import APIRouter, Form, HTTPException

router = APIRouter()

AUDIT_HELPER = "/usr/local/bin/tiersense_audit_config.sh"

@router.post("/configure-monitoring")
async def configure_monitoring(target_dir: str = Form(...)):
    """
    Set auditd monitoring on the specified directory by calling a host-level helper script.
    The directory path is received in container-space (/host-root/...), and mapped to host-space.
    """
    target_dir = target_dir.strip()

    # 1. Verify the container-level path exists
    if not os.path.exists(target_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Path not found inside container: '{target_dir}'. Ensure it is mounted correctly."
        )

    # 2. Translate to actual host path by stripping the /host-root prefix
    host_path = target_dir.replace("/host-root", "", 1)

    # 3. Ensure the helper script exists
    if not os.path.exists(AUDIT_HELPER):
        raise HTTPException(
            status_code=500,
            detail=f"Audit configuration helper script missing at {AUDIT_HELPER}."
        )

    try:
        # 4. Call the host audit helper script with sudo
        result = subprocess.run(
            ["sudo", AUDIT_HELPER, "add", host_path],
            capture_output=True,
            text=True,
            check=True
        )
        return {
            "status": "success",
            "message": f"Auditd monitoring configured for host path: {host_path}",
            "stdout": result.stdout.strip()
        }

    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Audit configuration failed: {e.stderr.strip() if e.stderr else 'Unknown error'}"
        )