#!/bin/bash
# tiersense_audit_config.sh

ACTION=$1
WATCH_DIR=$2

AUDIT_RULE="always,exit -F dir=${WATCH_DIR} -F perm=rwa -F key=tiersense_monitoring"

if [[ "$ACTION" == "add" ]]; then
    sudo auditctl -a $AUDIT_RULE
    echo "[INFO] Added audit rule for $WATCH_DIR"
elif [[ "$ACTION" == "remove" ]]; then
    sudo auditctl -d $AUDIT_RULE
    echo "[INFO] Removed audit rule for $WATCH_DIR"
else
    echo "Usage: $0 {add|remove} /path/to/dir"
    exit 1
fi