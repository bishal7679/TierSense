#!/bin/bash

set -e

# Configuration
EXPORT_DIR="/nfs/logs"
EXPORT_CLIENT="*" # You can set to specific IP or CIDR like 192.168.1.0/24

echo "🛠 Installing NFS server..."
sudo apt update
sudo apt install -y nfs-kernel-server

echo "📁 Creating export directory at $EXPORT_DIR..."
sudo mkdir -p "$EXPORT_DIR"
sudo chown nobody:nogroup "$EXPORT_DIR"
sudo chmod 777 "$EXPORT_DIR"  # Adjust permissions as needed

echo "🔧 Configuring /etc/exports..."
EXPORT_ENTRY="$EXPORT_DIR $EXPORT_CLIENT(rw,sync,no_subtree_check,no_root_squash)"
grep -qxF "$EXPORT_ENTRY" /etc/exports || echo "$EXPORT_ENTRY" | sudo tee -a /etc/exports

echo "📤 Exporting NFS shares..."
sudo exportfs -a

echo "🔁 Restarting NFS server..."
sudo systemctl restart nfs-kernel-server

echo "✅ NFS server setup complete!"
echo "📦 Exported directory: $EXPORT_DIR"
echo "🌐 Accessible from: $EXPORT_CLIENT"
