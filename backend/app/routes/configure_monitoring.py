# app/routes/configure_monitoring.py

import os
import subprocess
from fastapi import APIRouter, Form, HTTPException

router = APIRouter()

@router.post("/configure-monitoring")
async def configure_monitoring(target_dir: str = Form(...)):
    try:
        # Normalize path
        target_dir = target_dir.strip()
        if not target_dir.startswith("/mnt/nfs/"):
            raise HTTPException(status_code=400, detail="Target directory must be under /mnt/nfs")

        # Apply audit rule
        rule = f"-w {target_dir} -p rwxa -k tiering_monitor"
        subprocess.run(["auditctl", "-D"], check=True)  # clear existing rules
        subprocess.run(["auditctl"] + rule.split(), check=True)

        # Write new Filebeat config
        filebeat_config = f"""
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/audit/audit.log
    processors:
      - decode_json_fields:
          fields: ["message"]
          target: ""
          overwrite_keys: true
    multiline.pattern: '^{{'
    multiline.negate: true
    multiline.match: after

output.file:
  path: "/app/logs"
  filename: "access-tiering.ndjson"
  codec.json:
    pretty: false
"""
        with open("/etc/filebeat/filebeat.yml", "w") as f:
            f.write(filebeat_config.strip())

        # Restart Filebeat
        subprocess.run(["pkill", "-f", "filebeat"], check=False)
        subprocess.Popen(["filebeat", "-e"])

        return {"status": "success", "message": f"Monitoring configured for {target_dir}"}

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Command failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
