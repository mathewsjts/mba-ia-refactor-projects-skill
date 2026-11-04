def completion_rate(done, total):
    return round((done / total) * 100, 2) if total > 0 else 0
