#!/bin/bash
# tiersense_audit_config.sh

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
    echo "[INFO] Adding audit rule for ${WATCH_DIR}..."
    auditctl -a always,exit -F dir="${WATCH_DIR}" -F perm=rwxa -F auid>=1000 -F auid!=4294967295
    echo "[✓] Audit rule added."

elif [[ "$ACTION" == "remove" ]]; then
    echo "[INFO] Removing audit rules matching ${WATCH_DIR}..."
    auditctl -l | grep "${WATCH_DIR}" | while read -r line; do
        rule_args=$(echo "$line" | sed 's/^-a /-d /')
        echo "[INFO] Removing rule: $rule_args"
        auditctl $rule_args
    done
    echo "[✓] Matching audit rules removed."

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
