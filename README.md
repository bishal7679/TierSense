# **TierSense: File Access Pattern to Tiering Advisor (LLM-Powered)**

---
<p align="center">
<img src="https://github.com/user-attachments/assets/ef229501-4a49-48b2-b06d-cee521be674a" alt="TierSense Logo" width="400" height="370"/>
</p>

*TierSense is an intelligent, LLM-powered advisor that helps optimize file storage across hot, warm, and cold tiers based on real-time access patterns. Think of it as a brain for your storage systems—analyzing file access logs and recommending exactly which files should live where.*
 
---
 
## 📌 Project Overview
 
TierSense transforms noisy file access logs into meaningful **tiering decisions**.
 
## 🧪 Tech Stack
 
- **Python + FastAPI** – Backend for parsing, heatmap, and LLM integration
- **Filebeat + auditd** – Real-time file access logging
- **NFS** – Log sharing from remote audit system
- **Matplotlib** – Heatmap generation
- **Next.js + TailwindCSS** – Interactive frontend dashboard
- **Docker** – Full containerized deployment
 
---
 
## 🚀 Features
 
- **Real-time file access simulation, logging & audit analysis via Filebeat**
- **Logs shared from remote NFS server**
- **Heatmap to visualize file access frequency**
- **LLM-powered storage tiering (HOT/WARM/COLD)**
- **Multiple LLM-powered advisory engines (OpenAI/Gemini/Claude/Llama/Deepseek)**
- **Full Dockerized deployment (NFS + Frontend + Backend)**

---

## 📁 Project Structure
```
TierSense/
├── backend/
│   ├── app/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── components/
│   ├── pages/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## 🔄 Project Pipeline

<img width="2534" height="541" alt="image-1" src="https://github.com/user-attachments/assets/506e1f36-688b-4aa5-bc12-1193c4c89915" />

---

## 🧠 Architecture Diagram
```
+----------------+       NFS Mount Point        +---------------------+
|   VM1 (NFS)    | <--------------------------- | Docker Containers   |
|                |                              |                     |
|  /nfs/logs     |<------ Filebeat Output ------| - Backend (FastAPI) |
|  (NFS Share)   |                              | - Frontend (Next.js)|
+----------------+                              +---------------------+
       ^                                                ^
       |                                                |
       |  (NFS Exported)                                |
       |                                                |
       |                                                |
+----------------+                                      |
|      VM2       |<-------------------------------------
|                |    Mounts NFS Share
| /var/log/...   |    (e.g., /mnt/nfs/logs on VM2)
|                |
+----------------+
```

---

## 🛠️ How to Use

### 1️⃣ Basic Setup Instructions

#### 🔧 Step 1: Set up two VMs
- **VM1 (Filebeat + NFS Server):**
  - Runs Filebeat to capture logs
  - Hosts parsed logs in `/nfs/logs`

- **VM2 (App Host + NFS Client):**
  - Hosts **Frontend** and **Backend** containers
  - Mounts `/nfs/logs` from VM1 at `/var/log/sharedlogs`

#### 🪵 Filebeat Setup (on VM1)
- Already configured via `basic-setup.sh`
- Ensure it exports logs in `.ndjson` format to `/nfs/logs/`

#### 📦 NFS Server Setup (on VM1)
```bash
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
```
### NFS Client Setup on VM2
```bash
sudo mkdir -p /var/log/sharedlogs
sudo apt update
sudo apt install nfs-common -y
```
#### 🔄 Make mount persistent on VM2
```bash
# One-time mount
sudo mount <VM1-IP>:/nfs/logs /var/log/sharedlogs

# Make it persistent
sudo bash -c 'echo "<VM1-IP>:/nfs/logs /var/log/sharedlogs nfs defaults,_netdev,x-systemd.automount,noauto 0 0
" >> /etc/fstab'

```
Replace `<VM1-IP>` with the actual IP address of your VM1 (NFS host).

### 2️⃣ Audit Rules Setup
```bash
sudo auditctl -w /mnt/data -p war -k access_monitor
```

### 3️⃣ Docker Support Setup

#### 📦 docker-compose.yml
```yaml
version: '3.9'
services:
  backend:
    build:
      context: ./backend
    ports:
      - "8000:8000"
    volumes:
      - /var/log/sharedlogs:/var/log/sharedlogs

  frontend:
    build:
      context: ./frontend
    ports:
      - "3000:3000"
```

#### 🔥 Build and Run All at Once
```bash
docker compose build --no-cache
docker compose up
```
> Make sure VM2 has the NFS mount `/var/log/sharedlogs` pointing to VM1's `/nfs/logs`

---

## 💼 Business Use Cases

  - Reduce storage costs by demoting cold files to cheap media
  - Increase SSD utilization for high-performance files
  - Automate file lifecycle decisions
  - Plug into hybrid storage, cloud archiving, and NAS systems
 
---

## ✨ Challenges We Solved

  - Handling high-velocity file access logs in near real-time
  - Converting raw JSON into visual and AI-friendly format
  - Integrating with Gemini API to offload decision-making to LLMs
  - Making everything scriptable and automatable
    
## 📬 Contact
For any issues or enhancements, feel free to raise a GitHub issue or pull request. Happy tiering!
