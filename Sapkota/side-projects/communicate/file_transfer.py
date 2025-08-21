import os

DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "chat")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def save_file(filename, data):
    path = os.path.join(DOWNLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(data)
    return path
