import matplotlib.pyplot as plt 
from app.config import HEATMAP_PATH
import os

def generate_heatmap(access_counts):
    if not access_counts:
        print("No data to generate heatmap.")
        return

    files = list(access_counts.keys())
    counts = list(access_counts.values())

    fig, ax = plt.subplots(figsize=(10, len(files) * 0.4 + 1))
    ax.barh(files, counts, color='blue')
    ax.set_xlabel("Access Frequency")
    ax.set_title("File Access Heatmap (/mnt/data/*)")
    plt.tight_layout()

    # This ensures the parent directory exists
    os.makedirs(os.path.dirname(HEATMAP_PATH), exist_ok=True)

    plt.savefig(HEATMAP_PATH)
    print(f"[✔] Heatmap saved to: {HEATMAP_PATH}")
    plt.close()
