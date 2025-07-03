import random
from datetime import datetime

def simulate_random_access(file_paths, min_hits=1, max_hits=10):
    access_counts = {}
    access_times = {}

    for path in file_paths:
        hits = random.randint(min_hits, max_hits)
        access_counts[path] = hits
        access_times[path] = [datetime.now().isoformat()] * hits

    return access_counts, access_times
