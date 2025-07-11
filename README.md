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
 
- **Python** (Data pipeline, heatmap, LLM integration)
- **Filebeat** (Log shipping and monitoring)
- **Matplotlib / Pandas** (Heatmap generation)
- **Gemini/OpenAI GPT** (LLM-based recommendations)
- **Bash/CLI Tools** (Visualization and automation)
 
---
 
## 🚀 Features
 
- **Real-time file access simulation and logging**
- **Real-time audit log analysis via Filebeat**
- **File access pattern classification (hot/warm/cold)**
- **Heatmap generation to identify hot and cold files**
- **Visual output with heatmap**
- **LLM-driven tiering advice**
- **Multiple LLM-powered advisory engines (OpenAI/Gemini/Claude/Llama/Deepseek)**
- **Cloud tier recommendation**
- **Easy integration into storage lifecycle and archive tools**
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

<img width="2534" height="717" alt="image" src="https://github.com/user-attachments/assets/d9e873b3-6002-4b7b-8f41-d7db880f3e4d" />


---

## 🧠 Architecture Diagram
```
                    ┌──────────────┐
                    │   VM1 (NFS)  │
                    │              │
                    │  /nfs/logs   │◄─── Filebeat Output
                    │              │
                    └─────▲────────┘
                          │   (NFS Mount)
                          │
                          ▼
┌──────────────┐   Mounts NFS   ┌──────────────────┐
│   VM2        │──────────────▶│ Docker Containers │
│              │               │                   │
│ /var/log/... │               │ - Backend (FastAPI)
│              │               │ - Frontend(nextjs)│
└──────────────┘               └────────────────── ┘
```

---

## 🛠️ How to Use

### 1️⃣ Basic Setup Instructions

#### 🔧 Step 1: Set up two VMs
- **VM1 (Filebeat + NFS Server):**
  - Runs Filebeat to capture logs
  - Hosts parsed logs in `/nfs/logs`

- **VM2 (App Host):**
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

#### 🔄 Make mount persistent on VM2
```bash
# One-time mount
sudo mount <VM1-IP>:/nfs/logs /var/log/sharedlogs

# Make it persistent
sudo bash -c 'echo "<VM1-IP>:/nfs/logs /var/log/sharedlogs nfs defaults 0 0" >> /etc/fstab'
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
