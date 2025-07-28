# backend/app/core/heatmap.py
import os
import logging
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime  # ← ADDED: Missing import that caused the error
from app.config import HEATMAP_PATH

logger = logging.getLogger(__name__)

def generate_heatmap(access_counts: dict, top_n: int = 50, title_suffix: str = "") -> str:
    """
    Generate heatmap with configurable top N filtering
    
    Args:
        access_counts: Dictionary of file paths and their access counts
        top_n: Number of top files to display (default 50, max 100)
        title_suffix: Additional text for the title (e.g., date)
    
    Returns:
        String path to the generated heatmap image file
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
        logger.warning("No items to display in heatmap after filtering")
        return ""
        
    paths, counts = zip(*items)
    
    # Enhanced color coding with more granular tiers
    colors = []
    for c in counts:
        if c >= 100:
            colors.append("#DC2626")  # Red - HOT
        elif c >= 50:
            colors.append("#EA580C")  # Orange-Red - Very Warm
        elif c >= 20:
            colors.append("#F59E0B")  # Orange - WARM
        elif c >= 10:
            colors.append("#10B981")  # Green - Cool
        else:
            colors.append("#3B82F6")  # Blue - COLD
    
    # Dynamic height based on number of items with better scaling
    height = max(len(paths) * 0.4 + 2, 6)  # Minimum height of 6
    width = max(14, len(str(max(counts))) * 0.5 + 12)  # Dynamic width based on count values
    
    fig, ax = plt.subplots(figsize=(width, height))
    
    # Create horizontal bar chart
    bars = ax.barh(range(len(paths)), counts, color=colors, alpha=0.8, edgecolor='white', linewidth=0.5)
    
    # Customize the plot
    ax.set_yticks(range(len(paths)))
    # Show only filename for better readability
    ax.set_yticklabels([os.path.basename(p) for p in paths], fontsize=9)
    ax.set_xlabel("Access Frequency", fontsize=11, fontweight='bold')
    
    # Enhanced title with better formatting
    title = f"File Access Heatmap - Top {len(paths)} Files"
    if title_suffix:
        title += f" ({title_suffix})"
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Add value labels on bars with better positioning
    max_count = max(counts)
    for i, (bar, count) in enumerate(zip(bars, counts)):
        # Position text inside bar if bar is wide enough, otherwise outside
        text_x = bar.get_width() - (max_count * 0.02) if bar.get_width() > max_count * 0.3 else bar.get_width() + (max_count * 0.01)
        text_color = 'white' if bar.get_width() > max_count * 0.3 else 'black'
        
        ax.text(text_x, bar.get_y() + bar.get_height()/2, 
                str(count), va='center', ha='right' if bar.get_width() > max_count * 0.3 else 'left',
                fontsize=8, fontweight='bold', color=text_color)
    
    # Enhanced legend with more detailed tiers
    legend = [
        mpatches.Patch(color='#DC2626', label='HOT (≥100)'),
        # mpatches.Patch(color='#EA580C', label='Very Warm (50-99)'),
        mpatches.Patch(color='#F59E0B', label='WARM (20-99)'),
        # mpatches.Patch(color='#10B981', label='Cool (10-19)'),
        mpatches.Patch(color='#3B82F6', label='COLD (<20)')
    ]
    ax.legend(handles=legend, loc='lower right', fontsize=9, framealpha=0.9)
    
    # Grid for better readability
    ax.grid(axis='x', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # Better margins and layout
    plt.tight_layout()
    plt.subplots_adjust(left=0.2, right=0.95, top=0.9, bottom=0.1)
    
    # Save with timestamp to avoid caching issues
    timestamp = int(datetime.now().timestamp())
    heatmap_filename = f"access_heatmap_{timestamp}.png"
    heatmap_path = os.path.join(os.path.dirname(HEATMAP_PATH), heatmap_filename)
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(heatmap_path), exist_ok=True)
    
    # Save with high quality
    plt.savefig(heatmap_path, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    
    logger.info("Heatmap saved to %s with %d files displayed", heatmap_path, len(paths))
    return heatmap_path

def cleanup_old_heatmaps(keep_count: int = 10):
    """
    Clean up old heatmap files, keeping only the most recent ones
    
    Args:
        keep_count: Number of recent heatmap files to keep
    """
    try:
        heatmap_dir = os.path.dirname(HEATMAP_PATH)
        if not os.path.exists(heatmap_dir):
            return
        
        # Find all heatmap files
        heatmap_files = [
            f for f in os.listdir(heatmap_dir) 
            if f.startswith("access_heatmap_") and f.endswith(".png")
        ]
        
        if len(heatmap_files) <= keep_count:
            return
        
        # Sort by modification time (newest first)
        heatmap_files.sort(
            key=lambda f: os.path.getmtime(os.path.join(heatmap_dir, f)), 
            reverse=True
        )
        
        # Remove old files
        for old_file in heatmap_files[keep_count:]:
            old_path = os.path.join(heatmap_dir, old_file)
            os.remove(old_path)
            logger.info("Removed old heatmap: %s", old_file)
            
    except Exception as e:
        logger.warning("Failed to cleanup old heatmaps: %s", e)
