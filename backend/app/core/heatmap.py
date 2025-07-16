import os
import matplotlib.pyplot as plt
from app.config import HEATMAP_PATH

def generate_heatmap(access_counts: dict):
    if not access_counts:
        print("[!] No data to generate heatmap.")
        return

    files = list(access_counts.keys())
    counts = list(access_counts.values())

    # Determine tier color based on access frequency
    def get_color(count):
        if count >= 100:
            return "red"     # HOT
        elif count >= 20:
            return "orange"  # WARM
        else:
            return "blue"    # COLD

    colors = [get_color(c) for c in counts]

    fig, ax = plt.subplots(figsize=(12, len(files) * 0.4 + 1))
    ax.barh(files, counts, color=colors)
    ax.set_xlabel("Access Frequency")
    ax.set_title("File Access Heatmap")
    plt.tight_layout()

    os.makedirs(os.path.dirname(HEATMAP_PATH), exist_ok=True)
    plt.savefig(HEATMAP_PATH)
    print(f"[✔] Heatmap saved to: {HEATMAP_PATH}")
    plt.close()
