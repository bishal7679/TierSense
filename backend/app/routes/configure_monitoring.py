import os
import subprocess
from fastapi import APIRouter, Form, HTTPException

router = APIRouter()
AUDIT_HELPER = "/usr/local/bin/tiersense_audit_config.sh"

@router.post("/configure-monitoring")
async def configure_monitoring(target_dir: str = Form(...)):
    """
    Sets auditd monitoring on a dynamically provided directory path.
    The path is passed as a container-mounted path (/host-root/...), and mapped to the host.
    """
    target_dir = target_dir.strip()

    # Step 1: Validate the path inside container
    if not os.path.exists(target_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Path not found in container: '{target_dir}'. Is it mounted under /host-root?"
        )

    # Step 2: Strip /host-root to get real host path
    if not target_dir.startswith("/host-root"):
        raise HTTPException(
            status_code=400,
            detail=f"Expected path to start with /host-root, got: '{target_dir}'"
        )

    host_path = target_dir.replace("/host-root", "", 1)

    # Step 3: Validate helper script
    if not os.path.exists(AUDIT_HELPER):
        raise HTTPException(
            status_code=500,
            detail=f"Audit helper script missing at {AUDIT_HELPER}."
        )

    try:
        result = subprocess.run(
            ["bash", AUDIT_HELPER, "add", host_path],
            capture_output=True,
            text=True,
            check=True
        )
        return {
            "status": "success",
            "host_path": host_path,
            "stdout": result.stdout.strip()
        }

    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Audit config failed: {e.stderr.strip() if e.stderr else 'Unknown error'}"
        )