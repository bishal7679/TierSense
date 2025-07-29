#!/bin/bash
# tiersense_audit_config.sh - FIXED VERSION

set -euo pipefail

ACTION=${1:-}
WATCH_DIR=${2:-}

function usage() {
    echo "Usage: $0 {add|remove|clear} /path/to/dir"
    exit 1
}

if [[ -z "$ACTION" ]]; then
    usage
fi

if [[ "$ACTION" == "add" || "$ACTION" == "remove" ]]; then
    if [[ -z "$WATCH_DIR" || ! -d "$WATCH_DIR" ]]; then
        echo "[ERROR] Invalid or missing directory: '$WATCH_DIR'"
        usage
    fi
fi

if [[ "$ACTION" == "add" ]]; then
    echo "[INFO] Adding file-watch audit rule for ${WATCH_DIR}..."
    auditctl -w "${WATCH_DIR}" -p rwxa -k tiersense
    echo "[✓] File-watch audit rule added."

elif [[ "$ACTION" == "remove" ]]; then
    echo "[INFO] Removing file-watch rules for ${WATCH_DIR}..."
    auditctl -W "${WATCH_DIR}" -p rwxa -k tiersense || echo "[WARNING] Rule may not exist"
    echo "[✓] File-watch rules removed."

elif [[ "$ACTION" == "clear" ]]; then
    echo "[INFO] Clearing all audit rules..."
    auditctl -D
    echo "[✓] All audit rules cleared."

else
    usage
fi

echo
echo "[INFO] Current audit rules:"
auditctl -l
