import math

def format_eta(seconds: float) -> str:
    """Format ETA seconds into H:M:S string."""
    seconds = max(int(seconds), 0)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}h {m}m {s}s"
    elif m > 0:
        return f"{m}m {s}s"
    else:
        return f"{s}s"


def get_progress_bar(percent: float, length: int = 20) -> str:
    """
    Return a simple text progress bar.
    Example: [██████░░░░░░░░░░] 30%
    """
    percent = max(0, min(100, percent))
    filled_length = math.floor(length * percent / 100)
    empty_length = length - filled_length
    bar = "█" * filled_length + "░" * empty_length
    return f"[{bar}] {percent:.1f}%"
