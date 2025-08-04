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

+----------------+            +------------------------+
|   VM1 (NFS)    | <--------- | Docker Host (VM2)      |
| /nfs/logs      |   NFS Mt   |                        |
| (audit logs)   |  → /mnt/nfs| ┌───────────────────┐  |
+----------------+            | │ Backend (FastAPI) │  |
                              | │ Frontend (Next.js)│  |
                              | └───────────────────┘  |
                              +------------------------+
 


```
 
---

## 🧪 Tech Stack
 
- Backend: Python, FastAPI, Uvicorn
- Logging: auditd, Filebeat → NDJSON
- Storage: NFS share for log collection
- Visualization: Matplotlib heatmaps
- Frontend: Next.js, TailwindCSS
- AI: Gemini, GPT, Claude, Ollama, DeepSeek
- Deployment: Docker Compose, daily reset scheduler with Schedule

---

## 🚀 Features

- Real-Time Tracking: Continuous file-access capture via Filebeat
- Daily Reset: Automatic midnight reset; historical retention for 7 days
- Heatmaps: Top-N file access bar charts with dynamic coloring tiers
- LLM Integration: JSON-only prompts classify files to HOT/WARM/COLD
- Dynamic Tier Ranges: Loadable from config for custom thresholds
- Historical Data: SQLite storage of daily summaries and counts
- Manual Controls: API endpoints for manual reset and audit rule configuration
- Security: Audit rule helper script for host-side syscall monitoring

---

## 📁 Project Structure
 
```

TierSense/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── parser.py
│   │   │   ├── heatmap.py
│   │   │   ├── daily_reset.py
│   │   │   ├── historical.py
│   │   │   └── llm_factory.py
│   │   ├── routes/
│   │   │   ├── run.py
│   │   │   ├── settings.py
│   │   │   └── configure_monitoring.py
│   │   ├── main.py
│   │   ├── config.py
│   │   └── settings.json
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── components/
│   ├── pages/
│   ├── public/
│   ├── styles/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md

```

---

## 🛠️ How to Use

### 1️⃣ Basic Setup Instructions
#### 📦 Prerequisite

```
- Linux VM with auditd, NFS
- Docker & Docker Compose
```

## 1. Setup NFS Server (VM1 / Terminal1)

`Run the` [setup_nfs_server.sh](https://github.com/bishal7679/TierSense/blob/main/setup_nfs_server.sh) `script to install required tools and Filebeat`

## 2.Setup Host Audit Config

`Run the` [prepare_host.sh](https://github.com/bishal7679/TierSense/blob/main/prepare_host.sh) `script to install required tools and Filebeat`
 
## 3. Deploy TierSense (VM2 / Terminal2)

```
docker compose build --no-cache
docker compose up -d
```
`Ensure /nfs/logs is mounted to /mnt/nfs inside the backend container.`

## 🌡 Heatmap Sample Output
<img width="500" height="200" alt="Screenshot 2025-07-14 112214" src="https://github.com/user-attachments/assets/c7d76557-3cb7-4787-aed0-b05ea28314c2" />

`These visuals give you an intuitive idea of how your data is being used—and how it should be stored.`

View the heatmap result:
 
```bash

sudo xdg-open /var/log/sharedlogs/access-heatmap.png

```

This will display the visual heatmap that reflects your file usage patterns 📊.
 
---

## 💼 Business Use Cases
 
- Cost Savings: Automatically archive rarely accessed “COLD” files to low-cost storage (e.g., S3 Glacier), cutting storage bills by up to 40%.
- Performance: Promote “HOT” files—like active session logs—to SSD pools for sub-millisecond access during peak loads.
- Automation: Schedule daily tiering so files move between tiers automatically, freeing your ops team from manual housekeeping.
- Insights: Review heatmaps and AI recommendations to spot unusual access spikes—ideal for security audits and capacity planning.
 
---

## ✨ Highlights

- Dynamic Thresholds: Tune HOT/WARM/COLD ranges via simple JSON config—no code changes required.
- LLM-Driven: Plug in Gemini, GPT, Claude, or on-prem Ollama for context-aware tiering decisions.
- Extensible: Add new LLMs or swap Matplotlib for Grafana/Plotly with minimal effort.
- Scalable: Handles millions of daily audit events, purges stale logs, and resets counts at midnight.

---

## 📬 Contributing & Support

TierSense is open-source—submit issues or PRs on GitHub. For enterprise needs (SLA support, custom integrations, on-site workshops), contact the core maintainers. Happy tiering!
 
