# mission/telemetry.py

def format_time(seconds):
    if seconds < 0:
        mins = int(abs(seconds) // 60)
        secs = int(abs(seconds) % 60)
        return f"T- {mins:02}:{secs:02}"
    else:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"T+ {mins:02}:{secs:02}"
