#!/bin/bash
# TierSense Host Preparation Script
# This script ensures that the necessary host-level dependencies (auditd) are installed and running.
# It should be run once with sudo before the first 'docker-compose up'.

set -e

echo "[+] Welcome to the TierSense Host Preparation."
echo "[+] This script will check for and install the 'auditd' service, which is required for file monitoring."

# --- Check for root/sudo privileges ---
if [ "$EUID" -ne 0 ]; then
  echo "[!] Please run this script with sudo: sudo ./prepare_host.sh"
  exit 1
fi

# --- Detect Package Manager and Install auditd ---
if command -v apt-get &> /dev/null; then
    # Debian/Ubuntu
    echo "[i] Detected Debian/Ubuntu based system."
    echo "[+] Installing auditd and enabling the service..."
    apt-get update
    apt-get install -y auditd audispd-plugins
    systemctl enable auditd --now
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    echo "[i] Detected RHEL/CentOS based system."
    echo "[+] Installing auditd and enabling the service..."
    yum install -y audit
    systemctl enable auditd --now
elif command -v dnf &> /dev/null; then
    # Fedora
    echo "[i] Detected Fedora based system."
    echo "[+] Installing auditd and enabling the service..."
    dnf install -y audit
    systemctl enable auditd --now
else
    echo "[✗] ERROR: Could not detect a supported package manager (apt, yum, dnf)."
    echo "[!] Please manually install 'auditd' on your system and ensure the service is running."
    exit 1
fi

# --- Verify Service Status ---
if systemctl is-active --quiet auditd; then
    echo "[✓] The auditd service is now active and running."
    echo "[✓] Host preparation complete! You can now run 'docker-compose up --build'."
else
    echo "[✗] ERROR: The auditd service failed to start."
    echo "[!] Please check the service status with 'sudo systemctl status auditd'."
    exit 1
fi