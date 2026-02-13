import time

def format_eta(seconds):
    minutes, sec = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {sec}s"
    elif minutes > 0:
        return f"{minutes}m {sec}s"
    else:
        return f"{sec}s"

def get_progress_bar(percent, length=10):
    filled_length = int(length * percent // 100)
    bar = "█" * filled_length + "░" * (length - filled_length)
    return f"[{bar}] {percent:.2f}%"
