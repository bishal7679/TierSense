#!/bin/bash
set -e

# === CONFIG ===
EXPORT_DIR="/nfs/logs"
EXPORT_CLIENT="*"  # Or use IP/CIDR like 192.168.1.0/24
EXPORT_RULE="$EXPORT_DIR $EXPORT_CLIENT(rw,sync,no_subtree_check,no_root_squash)"

echo "[+] Installing NFS server..."
apt update
apt install -y nfs-kernel-server

echo "[+] Creating export directory: $EXPORT_DIR"
mkdir -p "$EXPORT_DIR"
chown nobody:nogroup "$EXPORT_DIR"
chmod 777 "$EXPORT_DIR"  # Adjust permissions if needed

echo "[+] Checking /etc/exports..."
if ! grep -qxF "$EXPORT_RULE" /etc/exports; then
    echo "$EXPORT_RULE" >> /etc/exports
    echo "[✓] Rule added: $EXPORT_RULE"
else
    echo "[✓] Rule already present"
fi

echo "[+] Applying export rules..."
exportfs -ra

echo "[+] Restarting NFS service..."
systemctl restart nfs-kernel-server

echo "[✓] NFS server setup complete!"
echo "    Shared: $EXPORT_DIR"
echo "    Access: $EXPORT_CLIENT"