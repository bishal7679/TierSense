#!/bin/bash
 
set -e
 
echo ">> Installing dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip auditd filebeat curl
 
echo ">> Installing Python packages..."
pip3 install -r requirements.txt
 
echo ">> Configuring auditd rules..."
sudo auditctl -w /mnt/data -p rwxa -k file_access
 
echo ">> Configuring Filebeat..."
sudo cp filebeat.yml /etc/filebeat/filebeat.yml
sudo systemctl enable filebeat
sudo systemctl restart filebeat
sudo systemctl status filebeat --no-pager
 
echo ">> Setup complete. Filebeat is monitoring /mnt/data"
