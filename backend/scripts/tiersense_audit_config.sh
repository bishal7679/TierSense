#!/bin/bash
# Script to manage auditd rules from inside the container (via mounted host)

ACTION="$1"
DIR="$2"

if [[ "$ACTION" == "add" && -n "$DIR" ]]; then
    auditctl -D
    auditctl -a always,exit -F dir="$DIR" -F perm=rwxa -F auid>=1000 -F auid!=4294967295 -k tiersense
    echo "Audit rule added for directory: $DIR"
elif [[ "$ACTION" == "clear" ]]; then
    auditctl -D
    echo "Audit rules cleared"
else
    echo "Usage:"
    echo "  $0 add /path/to/monitor"
    echo "  $0 clear"
    exit 1
fi