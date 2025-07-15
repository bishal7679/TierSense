from fastapi import APIRouter, HTTPException
import os
import subprocess

router = APIRouter()

AUDIT_RULE_KEY = "access_monitor"
CONFIG_FILE = "/app/config/selected_path.txt"

@router.post("/set-directory")
def set_directory(path: str):
    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail="Invalid directory path")

    # Remove old audit rule (if exists)
    subprocess.run(["auditctl", "-W", path, "-k", AUDIT_RULE_KEY], stdout=subprocess.PIPE)

    # Apply new audit rule
    result = subprocess.run(["auditctl", "-w", path, "-p", "war", "-k", AUDIT_RULE_KEY], stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=result.stderr.decode())

    # Save path in config
    with open(CONFIG_FILE, "w") as f:
        f.write(path)

    return {"message": "Audit rule applied successfully", "path": path}
