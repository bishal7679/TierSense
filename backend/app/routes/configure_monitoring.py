import os
import subprocess
from fastapi import APIRouter, Form, HTTPException

router = APIRouter()
AUDIT_KEY = "tiersense_monitoring"

@router.post("/configure-monitoring")
async def configure_monitoring(target_dir: str = Form(...)):
    """
    Applies a syscall-based auditctl rule for the selected directory
    to capture read/write accesses with full path context.
    """
    target_dir = target_dir.strip()

    # Validate container path
    if not os.path.exists(target_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Path not found in container: '{target_dir}'. Is it mounted under /host-root?"
        )

    # Validate prefix
    if not target_dir.startswith("/host-root"):
        raise HTTPException(
            status_code=400,
            detail=f"Expected path to start with /host-root, got: '{target_dir}'"
        )

    # Get the host path
    host_path = target_dir.replace("/host-root", "", 1)

    if not os.path.exists("/sbin/auditctl"):
        raise HTTPException(
            status_code=500,
            detail="auditctl not found. Is auditd installed and running?"
        )

    try:
        # Remove any old rules for this key
        subprocess.run(["auditctl", "-D"], check=True)

        # Apply new syscall-based rule
        rule = [
            "auditctl", "-a", "always,exit",
            "-F", f"dir={host_path}",
            "-F", "perm=rwa",
            "-F", "auid>=1000",
            "-F", "auid!=4294967295",
            "-k", AUDIT_KEY
        ]
        result = subprocess.run(rule, capture_output=True, text=True, check=True)

        return {
            "status": "success",
            "host_path": host_path,
            "stdout": result.stdout.strip() or "Rule applied successfully."
        }

    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to apply audit rule: {e.stderr.strip() if e.stderr else 'Unknown error'}"
        )