import os
import sys
import time
import subprocess
import webbrowser
import threading
import socket
import uvicorn

PORT = 5000
HOST = "0.0.0.0"

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0

def open_website(url: str):
    """
    Opens the website in the user's default web browser.
    """
    time.sleep(1.0)
    print(f"[VideoFetcher] Opening website in your default browser at: {url}")
    webbrowser.open(url)

def main():
    local_ip = get_local_ip()
    local_url = f"http://127.0.0.1:{PORT}"
    mobile_url = f"http://{local_ip}:{PORT}"

    print("=" * 65)
    print("     VideoFetcher - Universal Social Media Video Downloader      ")
    print("=" * 65)
    print(f"💻 Local (This PC):         {local_url}")
    print(f"📱 Mobile Phones & Tablets: {mobile_url}")
    print("=" * 65)
    print("💡 To open on your Mobile Phone:")
    print(f"   Connect your phone to the same Wi-Fi and open:")
    print(f"   👉 {mobile_url}")
    print("=" * 65)
    print("Starting server...")

    threading.Thread(target=open_website, args=(local_url,), daemon=True).start()
    uvicorn.run("server:app", host=HOST, port=PORT, log_level="warning")

if __name__ == "__main__":
    main()
