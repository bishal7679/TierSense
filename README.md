# **TierSense: File Access Pattern to Tiering Advisor (LLM-Powered)**

---
<p align="center">
<img src="https://github.com/user-attachments/assets/ef229501-4a49-48b2-b06d-cee521be674a" alt="TierSense Logo" width="430" height="380"/>
</p>

*TierSense is an intelligent, LLM-powered advisor that helps optimize file storage across hot, warm, and cold tiers based on real-time access patterns. Think of it as a brain for your storage systems—analyzing file access logs and recommending exactly which files should live where.*
 
---
 
## 📌 Project Overview
 
TierSense transforms noisy file access logs into meaningful **tiering decisions**.
 
### ⚙️ Key Pipeline:

```
Logs → Parser → Heatmap → LLM Suggestion → Tiering Advice
```
- **Logs:** Captured using Filebeat from simulated or real environments.

- **Parser:** Converts CSV logs into structured data.

- **Heatmap:** Aggregates file usage patterns.

- **LLM:** (Gemini/OpenAI) gives tiering advice—hot, warm, or cold—based on usage.

- **Visualization:** Heatmap output to help human users too.
 
---
 
## 🧪 Tech Stack
 
- **Python** (Data pipeline, heatmap, LLM integration)

- **Filebeat** (Log shipping and monitoring)

- **Matplotlib / Pandas** (Heatmap generation)

- **Gemini/OpenAI GPT** (LLM-based recommendations)

- **Bash/CLI Tools** (Visualization and automation)
 
---
 
## 🚀 Features
 
- Real-time file access simulation and logging

- Heatmap generation to identify hot and cold files

- LLM-driven tiering advice

- Visual output with heatmap

- Easy integration into storage lifecycle and archive tools
 
---
 
## 🧰 How to Set Up Locally
 
### ✅ Prerequisites:
 
- Python 3.9+

- Filebeat 8+

- `pip install -r requirements.txt`

- Export your Gemini/OpenAI API Key:
 
```bash

export GEMINI_API_KEY=your_key_here

```
 
---

## 🛠 How to Run

Run the parser + tiering pipeline:
 
```bash

sudo -E python3 tiering-advisor.py

```

View the heatmap result:
 
```bash

sudo xdg-open /var/log/filebeat_output/access-heatmap.png

```
This will display the visual heatmap that reflects your file usage patterns.

---

## 📊 Heatmap Sample Output

<p align="center">
<img src="https://github.com/user-attachments/assets/a82ffe0c-84fd-4049-add4-eabc80040cf2" alt="access_heatmap" width="800" height="400"/>
</p>

These visuals give you an intuitive idea of how your data is being used—and how it should be stored.
 
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
