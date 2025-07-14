# **TierSense: File Access Pattern to Tiering Advisor (LLM-Powered)**
<p align="center">
<img src="https://github.com/user-attachments/assets/ef229501-4a49-48b2-b06d-cee521be674a" alt="TierSense Logo" width="400" height="370"/>
</p>
 
*TierSense is an intelligent, LLM-powered advisor that helps optimize file storage across hot, warm, and cold tiers based on real-time access patterns. Think of it as a brain for your storage systems—analyzing file access logs and recommending exactly which files should live where.*

---

## 📌 Project Overview

TierSense transforms noisy file access logs into meaningful **tiering decisions**.
 
---

## ⚙️ Key Pipeline:
 
<img width="2534" height="541" alt="pipeline" src="https://github.com/user-attachments/assets/ea4dbfbb-e370-4dc6-8bc1-8fc2f8ae353f" />
 
---
 
## 🔄 Architecture
 
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
 
## 🧪 Tech Stack

- Python + FastAPI – Backend for parsing, heatmap, and LLM integration
- Filebeat + auditd – Real-time file access logging & monitoring
- NFS – Log sharing from remote audit system
- Matplotlib – Heatmap generation
- Next.js + TailwindCSS – Interactive frontend dashboard
- Docker – Full containerized deployment
 
---
 
## 🚀 Features
 
- Real-time file access tracking via Filebeat
- Logs shared from remote NFS server
- Heatmap to visualize file access frequency 
- Supports multiple LLMs with rule-based classification (HOT/WARM/COLD)
- Web UI for analysis, heatmap, and tiering output
- Fully dockerized (frontend + backend)
 
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
 
## 🛠️ How to Use
 
### 1️⃣ Basic Setup Instructions
 
#### 📦 Prerequisite

`Run the` [setup.sh](https://github.com/bishal7679/TierSense/blob/main/setup.sh) `script to install required tools and Filebeat`
 
#### 🖥️ VM Design

- **VM1 (NFS Server + Filebeat):**
  
  - Hosts audit logs in `/nfs/logs`
  - Runs Filebeat to parse logs and save to `/nfs/logs`
 
- **VM2 (NFS Client + App Host):**
  
  - Hosts **Frontend** and **Backend** containers.
  - Mounts `/nfs/logs` from VM1 at `/var/log/sharedlogs`
 
#### 📦 NFS Server Setup (on VM1)

`Run the` [setup_nfs_server.sh](https://github.com/bishal7679/TierSense/blob/main/setup_nfs_server.sh) `script to successfully set up the NFS server`
 
#### 📦 NFS Client Setup (on VM2)

```bash
sudo apt update
sudo apt install nfs-common -y

```
 
#### 🔄 Make mount persistent on VM2

```bash
# One-time mount
sudo mount <VM1-IP>:/nfs/logs /var/log/sharedlogs
 
# Make it persistent
sudo bash -c 'echo "<VM1-IP>:/nfs/logs /var/log/sharedlogs nfs defaults,_netdev,x-systemd.automount,noauto 0 0" >> /etc/fstab'

```

Replace `<VM1-IP>` with your VM1 (NFS Server) IP.
 
#### 🎯 Audit Rules Setup (on VM2)

```bash
sudo auditctl -w /mnt/data -p war -k access_monitor
```
 
> 🔁 Replace `<VM1-IP>` with your NFS server IP in the backend Dockerfile to ensure audit logs are read from the correct path.
 
### 2️⃣ Docker Deployment
 
#### 🔥 Build and Run All at Once

```bash
docker compose build --no-cache
docker compose up

```
 
> This will spin up both the backend and frontend containers in VM2. Ensure `/var/log/sharedlogs` is correctly mounted to access audit logs from VM1.
 
---
 
## 🌡 Heatmap Sample Output
 
<img width="500" height="200" alt="Screenshot 2025-07-14 112214" src="https://github.com/user-attachments/assets/c7d76557-3cb7-4787-aed0-b05ea28314c2" />
 
> These visuals give you an intuitive idea of how your data is being used—and how it should be stored.
 
View the heatmap result:

```bash
sudo xdg-open /var/log/sharedlogs/access-heatmap.png
```
This will display the visual heatmap that reflects your file usage patterns 📊.

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
 
---
 
## 📬 Contact
For any issues or enhancements, feel free to raise a GitHub issue or pull request. Happy tiering!
 
 
