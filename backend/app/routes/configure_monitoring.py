import os
import subprocess
from fastapi import APIRouter, Form, HTTPException

router = APIRouter()
AUDIT_HELPER = "/usr/local/bin/tiersense_audit_config.sh"

@router.post("/configure-monitoring")
async def configure_monitoring(target_dir: str = Form(...)):
    """
    Applies syscall-based audit rule on the host via helper script.
    Expects target_dir like /host-root/mnt/data
    """
    target_dir = target_dir.strip()

    # Step 1: Validate container path
    if not os.path.exists(target_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Path not found in container: '{target_dir}'. Is it mounted under /host-root?"
        )

    # Step 2: Must start with /host-root
    if not target_dir.startswith("/host-root"):
        raise HTTPException(
            status_code=400,
            detail=f"Expected path to start with /host-root, got: '{target_dir}'"
        )

    # Step 3: Convert to host path
    host_path = target_dir.replace("/host-root", "", 1)

    # Step 4: Ensure helper script exists
    if not os.path.exists(AUDIT_HELPER):
        raise HTTPException(
            status_code=500,
            detail=f"Audit helper script not found: {AUDIT_HELPER}"
        )

    # Step 5: Apply rule via host script
    try:
        result = subprocess.run(
            ["sudo", AUDIT_HELPER, "add", host_path],
            capture_output=True,
            text=True,
            check=True
        )

        return {
            "status": "success",
            "host_path": host_path,
            "stdout": result.stdout.strip() or "Audit rule applied successfully."
        }

    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Audit rule failed: {e.stderr.strip() if e.stderr else 'Unknown error'}"
        )