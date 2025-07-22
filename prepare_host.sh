#!/bin/bash

echo "[*] Starting host preparation for TierSense..."

# 1. Install auditd if not present
if ! command -v auditctl &> /dev/null; then
    echo "[+] Installing auditd..."
    sudo apt-get update && sudo apt-get install -y auditd
else
    echo "[*] auditd already installed."
fi

# 2. Ensure auditd is running
echo "[+] Ensuring auditd is enabled and running..."
sudo systemctl enable auditd
sudo systemctl start auditd

# 3. Create tiersense_audit_config.sh
AUDIT_HELPER_SCRIPT="/usr/local/bin/tiersense_audit_config.sh"

if [[ ! -f "$AUDIT_HELPER_SCRIPT" ]]; then
    echo "[+] Creating audit configuration helper script at $AUDIT_HELPER_SCRIPT"
    sudo tee "$AUDIT_HELPER_SCRIPT" > /dev/null << 'EOF'
#!/bin/bash
ACTION="$1"
DIR="$2"

if [[ "$ACTION" == "add" && -n "$DIR" ]]; then
    sudo auditctl -D
    sudo auditctl -a always,exit -F dir="$DIR" -F perm=rwxa -F auid>=1000 -F auid!=4294967295 -k tiersense
    echo "[✓] Audit rule added for directory: $DIR"
elif [[ "$ACTION" == "clear" ]]; then
    sudo auditctl -D
    echo "[✓] All audit rules cleared."
else
    echo "Usage: $0 add <directory> | clear"
    exit 1
fi
EOF
    sudo chmod +x "$AUDIT_HELPER_SCRIPT"
else
    echo "[*] Audit helper script already exists at $AUDIT_HELPER_SCRIPT"
fi

# 4. Add sudo NOPASSWD access for this script
if ! sudo grep -q "tiersense_audit_config.sh" /etc/sudoers; then
    echo "[+] Adding NOPASSWD sudo rule for audit config script..."
    echo "$(whoami) ALL=(ALL) NOPASSWD: $AUDIT_HELPER_SCRIPT" | sudo tee -a /etc/sudoers > /dev/null
else
    echo "[*] NOPASSWD rule for audit script already exists."
fi

echo "[✓] Host preparation complete."