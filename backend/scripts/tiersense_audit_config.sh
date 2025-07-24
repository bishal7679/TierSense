#!/bin/bash
# tiersense_audit_config.sh

set -euo pipefail

ACTION=${1:-}
WATCH_DIR=${2:-}
AUDIT_KEY="tiersense_monitoring"

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

    # Define the full audit rule
    AUDIT_RULE="-a always,exit -F dir=${WATCH_DIR} -F perm=rwxa -F auid>=1000 -F auid!=4294967295 -k ${AUDIT_KEY}"

    if [[ "$ACTION" == "add" ]]; then
        echo "[INFO] Adding audit rule for ${WATCH_DIR} with key '${AUDIT_KEY}'..."
        sudo auditctl $AUDIT_RULE
        echo "[✓] Audit rule added."

    elif [[ "$ACTION" == "remove" ]]; then
        echo "[INFO] Removing audit rule for ${WATCH_DIR}..."
        sudo auditctl -d $AUDIT_RULE
        echo "[✓] Audit rule removed."
    fi

elif [[ "$ACTION" == "clear" ]]; then
    echo "[INFO] Clearing all audit rules..."
    sudo auditctl -D
    echo "[✓] All audit rules cleared."

else
    usage
fi

echo
echo "[INFO] Current audit rules:"
sudo auditctl -l