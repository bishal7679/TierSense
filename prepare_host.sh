#!/bin/bash
# prepare_host.sh

set -e

echo "[*] Starting host preparation for TierSense..."

# 1. Ensure auditd is installed
if ! command -v auditctl &>/dev/null; then
    echo "[+] Installing auditd..."
    sudo apt-get update && sudo apt-get install -y auditd
else
    echo "[*] auditd already installed."
fi

# 2. Enable and start auditd service
echo "[+] Ensuring auditd is enabled and running..."
sudo systemctl enable auditd
sudo systemctl restart auditd

# 3. Create the audit config helper script
AUDIT_HELPER_SCRIPT="/usr/local/bin/tiersense_audit_config.sh"

if [[ ! -f "$AUDIT_HELPER_SCRIPT" ]]; then
    echo "[+] Creating helper script: $AUDIT_HELPER_SCRIPT"
    sudo tee "$AUDIT_HELPER_SCRIPT" > /dev/null << 'EOF'
#!/bin/bash
# tiersense_audit_config.sh

set -euo pipefail

ACTION=${1:-}
WATCH_DIR=${2:-}
RULES_FILE="/etc/audit/rules.d/tiersense.rules"

function usage() {
    echo "Usage: $0 {add|clear} /path/to/dir"
    exit 1
}

if [[ "$ACTION" == "add" ]]; then
    if [[ -z "$WATCH_DIR" || ! -d "$WATCH_DIR" ]]; then
        echo "[ERROR] Invalid or missing directory: '$WATCH_DIR'"
        usage
    fi

    echo "[+] Adding persistent audit rule for $WATCH_DIR..."

    # Write persistent syscall rule without key
    echo "-a always,exit -F dir=${WATCH_DIR} -F perm=rwxa -F auid>=1000 -F auid!=4294967295" | sudo tee "$RULES_FILE" > /dev/null

    sudo augenrules --load
    sudo systemctl restart auditd

    echo "[✓] Audit rule added and loaded."

elif [[ "$ACTION" == "clear" ]]; then
    echo "[+] Clearing TierSense audit rule..."
    sudo rm -f "$RULES_FILE"
    sudo augenrules --load
    sudo systemctl restart auditd
    echo "[✓] Audit rules removed."

else
    usage
fi
EOF

    sudo chmod +x "$AUDIT_HELPER_SCRIPT"
else
    echo "[*] Audit helper script already exists at $AUDIT_HELPER_SCRIPT"
fi

# 4. Add sudo NOPASSWD rule for the script if not present
if ! sudo grep -q "tiersense_audit_config.sh" /etc/sudoers; then
    echo "[+] Adding NOPASSWD rule for audit helper script..."
    echo "$(whoami) ALL=(ALL) NOPASSWD: $AUDIT_HELPER_SCRIPT" | sudo tee -a /etc/sudoers > /dev/null
else
    echo "[*] NOPASSWD rule already present."
fi

echo "[✓] Host preparation complete."
