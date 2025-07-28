# backend/app/core/heatmap.py
import os, logging
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from app.config import HEATMAP_PATH

logger = logging.getLogger(__name__)

def generate_heatmap(access_counts: dict, top_n: int = 50, title_suffix: str = "") -> str:
    """
    Generate heatmap with configurable top N filtering
    
    Args:
        access_counts: Dictionary of file paths and their access counts
        top_n: Number of top files to display (default 50, max 100)
        title_suffix: Additional text for the title (e.g., date)
    """
    if not access_counts:
        logger.warning("No data for heatmap")
        return ""

    # Limit top_n to reasonable bounds
    top_n = min(max(top_n, 10), 100)
    
    # Sort by access count (descending) and take top N
    items = sorted(access_counts.items(), key=lambda x: x[1], reverse=True)
    items = items[:top_n]
    
    if not items:
        return ""
        
    paths, counts = zip(*items)
    colors = ["red" if c >= 100 else "orange" if c >= 20 else "blue" for c in counts]
    
    # Dynamic height based on number of items
    height = len(paths) * 0.4 + 2
    fig, ax = plt.subplots(figsize=(14, height))
    
    # Create horizontal bar chart
    bars = ax.barh(range(len(paths)), counts, color=colors)
    
    # Customize the plot
    ax.set_yticks(range(len(paths)))
    ax.set_yticklabels([os.path.basename(p) for p in paths], fontsize=8)
    ax.set_xlabel("Access Frequency")
    
    # Enhanced title
    title = f"File Access Heatmap - Top {len(paths)} Files"
    if title_suffix:
        title += f" ({title_suffix})"
    ax.set_title(title, fontsize=12, fontweight='bold')
    
    # Add value labels on bars
    for i, (bar, count) in enumerate(zip(bars, counts)):
        ax.text(bar.get_width() + max(counts) * 0.01, bar.get_y() + bar.get_height()/2, 
                str(count), va='center', fontsize=7)
    
    # Legend
    legend = [
        mpatches.Patch(color='red', label='HOT (≥100)'),
        mpatches.Patch(color='orange', label='WARM (20–99)'),
        mpatches.Patch(color='blue', label='COLD (<20)')
    ]
    ax.legend(handles=legend, loc='lower right')
    
    plt.tight_layout()
    
    # Save with timestamp to avoid caching issues
    timestamp = int(datetime.now().timestamp())
    heatmap_filename = f"access_heatmap_{timestamp}.png"
    heatmap_path = os.path.join(os.path.dirname(HEATMAP_PATH), heatmap_filename)
    
    os.makedirs(os.path.dirname(heatmap_path), exist_ok=True)
    plt.savefig(heatmap_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info("Heatmap saved to %s", heatmap_path)
    return heatmap_path

