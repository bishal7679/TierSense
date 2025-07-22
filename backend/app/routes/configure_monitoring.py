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

    # 1. Check if path exists inside container
    if not os.path.exists(target_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Path not found inside container: '{target_dir}'. Ensure it is mounted correctly."
        )

    # 2. Convert container path (/host-root/...) → host path (/...)
    if not target_dir.startswith("/host-root"):
        raise HTTPException(
            status_code=400,
            detail="Expected path to start with /host-root (container-mounted host directory)."
        )
    host_path = target_dir.replace("/host-root", "", 1)

    # 3. Check helper script exists
    if not os.path.exists(AUDIT_HELPER):
        raise HTTPException(
            status_code=500,
            detail=f"Audit configuration helper script not found at {AUDIT_HELPER}"
        )

    # 4. Run the script without sudo (inside container)
    try:
        result = subprocess.run(
            ["bash", AUDIT_HELPER, "add", host_path],
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