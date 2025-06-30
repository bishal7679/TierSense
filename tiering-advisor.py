import os
import json
import re
import matplotlib.pyplot as plt
from collections import defaultdict
import google.generativeai as genai
 
# Load API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in environment")
 
genai.configure(api_key=GEMINI_API_KEY)
 
# Paths
LOG_DIR = "/var/log/filebeat_output"
HEATMAP_PATH = os.path.join(LOG_DIR, "access_heatmap.png")
 
# Regex for auditd PATH name
DATA_PATH_PATTERN = re.compile(r'name=(?:\\?"|")?(/mnt/data/[^"\\\s]+)')
 
# Parse audit logs from Filebeat output
def parse_logs(log_dir):
    access_counts = defaultdict(int)
    access_times = defaultdict(list)
    total_good, total_bad = 0, 0
 
    for filename in sorted(os.listdir(log_dir)):
        if not filename.endswith(".ndjson"):
            continue
 
        path = os.path.join(log_dir, filename)
        print(f"Processing file: {path}")
        good, bad = 0, 0
 
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    msg = data.get("message", "")
                    if "/mnt/data" not in msg:
                        continue
 
                    matches = DATA_PATH_PATTERN.findall(msg)
                    for match in matches:
                        access_counts[match] += 1
                        access_times[match].append(data.get("@timestamp", ""))
                    if matches:
                        good += 1
                except Exception:
                    bad += 1
 
        total_good += good
        total_bad += bad
        print(f" Parsed {good} good entries, Skipped {bad} bad entries.")
 
    print(f"\nFound {len(access_counts)} unique paths. Total good: {total_good}, bad: {total_bad}")
    return access_counts, access_times
 
# Generate and save heatmap
def generate_heatmap(access_counts):
    if not access_counts:
        print("No data for heatmap.")
        return
 
    files = list(access_counts.keys())
    counts = list(access_counts.values())
 
    fig, ax = plt.subplots(figsize=(10, len(files) * 0.4 + 1))
    ax.barh(files, counts, color='deepskyblue')
    ax.set_xlabel("Access Frequency")
    ax.set_title("File Access Heatmap (/mnt/data/*)")
    plt.tight_layout()
    plt.savefig(HEATMAP_PATH)
    print(f"Heatmap saved at: {HEATMAP_PATH}")
 
# Ask Gemini for tiering recommendations
def generate_gemini_tiering(access_counts):
    if not access_counts:
        print("No data to send to Gemini.")
        return
 
    prompt = (
        "You are a storage optimization system.\n"
        "Classify the following file paths into tiers:\n"
        "- HOT: Frequently accessed\n"
        "- WARM: Moderately accessed\n"
        "- COLD: Rarely accessed\n\n"
        "Output valid JSON like:\n"
        "{ \"/mnt/data/file1\": \"HOT\", \"/mnt/data/file2\": \"COLD\" }\n\n"
        "Access Frequencies:\n"
    )
    for path, count in sorted(access_counts.items(), key=lambda x: -x[1]):
        prompt += f"{path}: {count}\n"
 
    try:
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        response = model.generate_content(prompt)
        print("\n Gemini Tiering Output:\n", response.text.strip())
    except Exception as e:
        print(f"Gemini API call failed: {e}")
 
# Full pipeline
if __name__ == "__main__":
    access_counts, access_times = parse_logs(LOG_DIR)
    if access_counts:
        generate_heatmap(access_counts)
        generate_gemini_tiering(access_counts)
    else:
        print("No data to process.")
