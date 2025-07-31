# backend/app/core/heatmap.py

import os
import logging
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime
from app.config import HEATMAP_PATH, load_tier_ranges

logger = logging.getLogger(__name__)

def generate_heatmap(access_counts: dict, top_n: int = 50, title_suffix: str = "") -> str:
    """
    Generate heatmap with configurable top N filtering and dynamic tier coloring.
    """
    if not access_counts:
        logger.warning("No data for heatmap")
        return ""

    # Limit top_n bounds
    top_n = min(max(top_n, 10), 100)
    items = sorted(access_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    if not items:
        logger.warning("No items to display in heatmap after filtering")
        return ""

    paths, counts = zip(*items)
    ranges = load_tier_ranges()

    # Assign colors based on user-defined ranges
    colors = []
    for c in counts:
        min_h, max_h = ranges["HOT"]
        min_w, max_w = ranges["WARM"]
        min_c, max_c = ranges["COLD"]
        if min_h is not None and c >= min_h:
            colors.append("#DC2626")  # HOT
        elif ((min_w is None or c >= min_w) and
              (max_w is None or c < max_w)):
            colors.append("#F59E0B")  # WARM
        elif max_c is not None and c < max_c:
            colors.append("#3B82F6")  # COLD
        else:
            colors.append("#10B981")  # fallback

    # Dynamic figure size
    height = max(len(paths) * 0.35 + 3, 6)
    width = max(12, len(str(max(counts))) * 0.4 + 10)
    fig, ax = plt.subplots(figsize=(width, height))

    bars = ax.barh(range(len(paths)), counts, color=colors,
                   edgecolor='white', linewidth=0.8, height=0.7)

    # Y-axis labels
    labels = []
    for p in paths:
        fn = os.path.basename(p)
        labels.append(fn if len(fn) <= 25 else fn[:22] + "...")
    ax.set_yticks(range(len(paths)))
    ax.set_yticklabels(labels, fontsize=9)

    ax.set_xlabel("Access Frequency", fontsize=11, fontweight='bold')
    title = f"File Access Heatmap - Top {len(paths)} Files"
    if title_suffix:
        title += f" ({title_suffix})"
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

    # Bar labels
    max_count = max(counts)
    for bar, count in zip(bars, counts):
        if bar.get_width() > max_count * 0.4:
            x = bar.get_width() - max_count * 0.05
            color = 'white'; ha = 'right'
        else:
            x = bar.get_width() + max_count * 0.02
            color = 'black'; ha = 'left'
        ax.text(x, bar.get_y() + bar.get_height()/2, str(count),
                va='center', ha=ha, fontsize=8, fontweight='bold', color=color)

    # Legend using dynamic ranges
    legend_items = []
    for tier, (min_v, max_v) in ranges.items():
        if tier == "HOT":
            label = f"HOT (≥{min_v})" if min_v is not None else "HOT"
            color = "#DC2626"
        elif tier == "WARM":
            label = f"WARM ({min_v or 0}-{(max_v or '')})"
            color = "#F59E0B"
        else:  # COLD
            label = f"COLD (<{max_v})" if max_v is not None else "COLD"
            color = "#3B82F6"
        legend_items.append(mpatches.Patch(color=color, label=label))

    ax.legend(handles=legend_items, loc='lower right', fontsize=8, framealpha=0.95)

    ax.grid(axis='x', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.subplots_adjust(left=0.25, right=0.95, top=0.92, bottom=0.08)

    # Save with timestamp
    timestamp = int(datetime.now().timestamp())
    filename = f"access_heatmap_{timestamp}.png"
    path = os.path.join(os.path.dirname(HEATMAP_PATH), filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='white', pad_inches=0.1)
    plt.close()

    logger.info("Heatmap saved to %s with %d files displayed", path, len(paths))
    return f"/api/heatmap/{filename}"


def cleanup_old_heatmaps(keep_count: int = 10):
    """
    Remove old heatmap files, keeping only the most recent `keep_count`.
    """
    try:
        dir_ = os.path.dirname(HEATMAP_PATH)
        if not os.path.exists(dir_):
            return
        files = [f for f in os.listdir(dir_) if f.startswith("access_heatmap_") and f.endswith(".png")]
        if len(files) <= keep_count:
            return
        files.sort(key=lambda f: os.path.getmtime(os.path.join(dir_, f)), reverse=True)
        for old in files[keep_count:]:
            try:
                os.remove(os.path.join(dir_, old))
                logger.info("Removed old heatmap: %s", old)
            except OSError as e:
                logger.warning("Failed to remove %s: %s", old, e)
    except Exception as e:
        logger.warning("Failed to cleanup old heatmaps: %s", e)


def get_heatmap_stats(access_counts: dict) -> dict:
    """
    Compute basic statistics for heatmap metadata.
    """
    if not access_counts:
        return {"total_files": 0, "max_count": 0, "min_count": 0, "avg_count": 0}
    vals = list(access_counts.values())
    return {
        "total_files": len(vals),
        "max_count": max(vals),
        "min_count": min(vals),
        "avg_count": sum(vals) / len(vals)
    }