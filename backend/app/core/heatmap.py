# backend/app/core/heatmap.py

import os, logging
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from app.config import HEATMAP_PATH

logger = logging.getLogger(__name__)

def generate_heatmap(access_counts: dict) -> str:
    if not access_counts:
        logger.warning("No data for heatmap")
        return ""
    
    # FIXED: Sort by access count (descending) instead of filename
    # This ensures highest-access files are always displayed
    items = sorted(access_counts.items(), key=lambda x: x[1], reverse=True)
    paths, counts = zip(*items)
    colors = ["red" if c>=100 else "orange" if c>=20 else "blue" for c in counts]

    max_bars = 50
    bar_count = min(len(paths), max_bars)
    height = bar_count*0.4+1
    
    fig, ax = plt.subplots(figsize=(12, height))
    
    # Display the top N files (highest access counts first)
    ax.barh(paths[:bar_count], counts[:bar_count], color=colors[:bar_count])
    ax.set_xlabel("Access Frequency")
    ax.set_title("File Access Heatmap")
    
    legend = [
        mpatches.Patch(color='red', label='HOT (≥100)'),
        mpatches.Patch(color='orange', label='WARM (20–99)'),
        mpatches.Patch(color='blue', label='COLD (<20)')
    ]
    ax.legend(handles=legend, loc='lower right')
    plt.tight_layout()

    os.makedirs(os.path.dirname(HEATMAP_PATH), exist_ok=True)
    plt.savefig(HEATMAP_PATH, dpi=150)
    plt.close()
    logger.info("Heatmap saved to %s", HEATMAP_PATH)
    return HEATMAP_PATH
