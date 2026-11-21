import os
import re
import time
import uuid
import shutil
import urllib.parse
import threading
import logging
from typing import Dict, Any, Optional

import requests
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("VideoFetcher")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(APP_DIR, "downloads")
STATIC_DIR = os.path.join(APP_DIR, "static")

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

IS_SERVERLESS = bool(
    os.environ.get("AWS_LAMBDA_FUNCTION_NAME") or
    os.environ.get("NETLIFY") or
    os.environ.get("VERCEL") or
    os.environ.get("SERVERLESS")
)

app = FastAPI(title="VideoFetcher - Universal Social Media Video Downloader")

@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tasks_lock = threading.Lock()
tasks: Dict[str, Dict[str, Any]] = {}
download_history = []

def format_bytes(size: Optional[float]) -> str:
    if not size or size <= 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"

def format_duration(seconds: Optional[int]) -> str:
    if not seconds:
        return "00:00"
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def format_views(count: Optional[int]) -> str:
    if not count:
        return "0"
    if count >= 1_000_000_000:
        return f"{count / 1_000_000_000:.1f}B"
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    if count >= 1_000:
        return f"{count / 1_000:.1f}K"
    return str(count)

def detect_platform(url: str) -> Dict[str, str]:
    url_lower = url.lower()
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return {"name": "YouTube", "icon": "youtube", "color": "#FF0000"}
    elif "facebook.com" in url_lower or "fb.watch" in url_lower or "fb.com" in url_lower:
        return {"name": "Facebook", "icon": "facebook", "color": "#1877F2"}
    elif "instagram.com" in url_lower:
        return {"name": "Instagram", "icon": "instagram", "color": "#E4405F"}
    elif "tiktok.com" in url_lower:
        return {"name": "TikTok", "icon": "tiktok", "color": "#00F2FE"}
    elif "twitter.com" in url_lower or "x.com" in url_lower:
        return {"name": "X (Twitter)", "icon": "twitter", "color": "#1DA1F2"}
    elif "reddit.com" in url_lower or "redd.it" in url_lower:
        return {"name": "Reddit", "icon": "reddit", "color": "#FF4500"}
    elif "pinterest.com" in url_lower or "pin.it" in url_lower:
        return {"name": "Pinterest", "icon": "pinterest", "color": "#BD081C"}
    elif "vimeo.com" in url_lower:
        return {"name": "Vimeo", "icon": "vimeo", "color": "#1AB7EA"}
    elif "threads.net" in url_lower:
        return {"name": "Threads", "icon": "threads", "color": "#000000"}
    elif "linkedin.com" in url_lower:
        return {"name": "LinkedIn", "icon": "linkedin", "color": "#0A66C2"}
    elif "dailymotion.com" in url_lower:
        return {"name": "Dailymotion", "icon": "dailymotion", "color": "#0066DC"}
    elif "soundcloud.com" in url_lower:
        return {"name": "SoundCloud", "icon": "soundcloud", "color": "#FF5500"}
    else:
        return {"name": "Social Video", "icon": "video", "color": "#3B82F6"}

def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:120] if cleaned else "video"

class AnalyzeRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    format: str = "mp4" # "mp4", "mp3", "4k"
    quality: Optional[str] = "best" # "2160", "1080", "720", "480", "360", "best", "320k", "192k", "128k"

@app.post("/api/analyze")
def analyze_video(req: AnalyzeRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Please provide a valid video link")
    
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    platform = detect_platform(url)
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
        "js_runtimes": {"node": {}},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        err_msg = str(e)
        logger.error(f"Analysis error: {err_msg}")
        raise HTTPException(status_code=400, detail=f"Failed to extract video: {err_msg[:160]}")

    if not info:
        raise HTTPException(status_code=404, detail="No video information found")

    if "entries" in info and info["entries"]:
        info = info["entries"][0]

    title = info.get("title") or "Unknown Video"
    duration = info.get("duration") or 0
    thumbnail = info.get("thumbnail") or ""
    uploader = info.get("uploader") or info.get("channel") or platform["name"]
    views = info.get("view_count") or 0
    description = (info.get("description") or "")[:200]

    formats = info.get("formats", [])
    resolutions_map = {}
    best_audio_url = None
    best_progressive_url = None
    
    for f in formats:
        h = f.get("height")
        vcodec = f.get("vcodec")
        acodec = f.get("acodec")
        f_url = f.get("url")

        if vcodec != "none" and acodec != "none" and f_url:
            best_progressive_url = f_url

        if acodec != "none" and vcodec == "none" and f_url:
            best_audio_url = f_url

        if h and vcodec != "none":
            fsize = f.get("filesize") or f.get("filesize_approx")
            if not fsize and duration and f.get("tbr"):
                fsize = int((f.get("tbr") * 1024 / 8) * duration)

            if h not in resolutions_map or (fsize and not resolutions_map[h].get("filesize")):
                resolutions_map[h] = {
                    "height": h,
                    "ext": f.get("ext", "mp4"),
                    "filesize": fsize,
                    "fps": f.get("fps"),
                    "format_id": f.get("format_id"),
                    "url": f_url
                }

    available_resolutions = []
    for h in sorted(resolutions_map.keys(), reverse=True):
        label = f"{h}p"
        badge = ""
        if h >= 2160:
            label = "4K Ultra HD (2160p)"
            badge = "4K UHD"
        elif h >= 1440:
            label = "2K Quad HD (1440p)"
            badge = "2K QHD"
        elif h >= 1080:
            label = "Full HD (1080p)"
            badge = "1080p"
        elif h >= 720:
            label = "HD (720p)"
            badge = "720p"
        elif h >= 480:
            label = "SD (480p)"
            badge = "480p"
        elif h >= 360:
            label = "Medium (360p)"
            badge = "360p"
        else:
            label = f"Low ({h}p)"
            badge = f"{h}p"

        item = resolutions_map[h]
        size_str = format_bytes(item["filesize"]) if item["filesize"] else "Estimated Size"
        available_resolutions.append({
            "height": h,
            "label": label,
            "badge": badge,
            "size_str": size_str,
            "filesize": item["filesize"],
            "format_id": item["format_id"],
            "direct_url": item.get("url") or best_progressive_url
        })

    if not available_resolutions:
        available_resolutions.append({
            "height": 1080,
            "label": "Best Video Quality (Auto HD)",
            "badge": "HD",
            "size_str": "Auto Size",
            "filesize": 0,
            "format_id": "best",
            "direct_url": best_progressive_url or info.get("url")
        })

    audio_options = [
        {"quality": "320k", "label": "MP3 High Quality (320 kbps)", "badge": "320K HQ", "bitrate": 320, "direct_url": best_audio_url},
        {"quality": "192k", "label": "MP3 Standard (192 kbps)", "badge": "192K STD", "bitrate": 192, "direct_url": best_audio_url},
        {"quality": "128k", "label": "MP3 Compact (128 kbps)", "badge": "128K ECO", "bitrate": 128, "direct_url": best_audio_url},
    ]

    has_4k = any(r["height"] >= 2160 for r in available_resolutions)

    return {
        "id": info.get("id"),
        "url": url,
        "title": title,
        "duration": duration,
        "duration_str": format_duration(duration),
        "thumbnail": thumbnail,
        "uploader": uploader,
        "views": views,
        "views_str": format_views(views),
        "platform": platform,
        "description": description,
        "resolutions": available_resolutions,
        "audio_options": audio_options,
        "has_4k": has_4k,
        "default_height": available_resolutions[0]["height"] if available_resolutions else 720,
        "direct_url": best_progressive_url or info.get("url"),
        "is_serverless": IS_SERVERLESS
    }

def run_download_thread(task_id: str, url: str, fmt: str, quality: str):
    task_dir = os.path.join(DOWNLOADS_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    with tasks_lock:
        tasks[task_id].update({
            "status": "downloading",
            "percent": 0.0,
            "speed": "0 KB/s",
            "eta": "--",
            "downloaded": "0 B",
            "total": "--",
            "message": "Initializing download..."
        })

    def progress_hook(d):
        with tasks_lock:
            task = tasks.get(task_id)
            if not task:
                return

            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes", 0)
                speed = d.get("speed") or 0
                eta = d.get("eta") or 0

                percent = 0.0
                if total > 0:
                    percent = (downloaded / total) * 100
                elif "_percent_str" in d:
                    try:
                        p_str = re.sub(r"[^\d.]", "", d["_percent_str"])
                        percent = float(p_str)
                    except Exception:
                        percent = 50.0

                task["status"] = "downloading"
                task["percent"] = min(round(percent, 1), 98.0)
                task["speed"] = f"{format_bytes(speed)}/s" if speed else "Downloading..."
                task["eta"] = f"{eta}s" if eta else "--"
                task["downloaded"] = format_bytes(downloaded)
                task["total"] = format_bytes(total) if total else "Calculating..."
                task["message"] = "Downloading stream..."
            elif d["status"] == "finished":
                task["status"] = "processing"
                task["percent"] = 99.0
                task["message"] = "Merging audio & video with FFmpeg..."

    out_template = os.path.join(task_dir, "%(title).100s.%(ext)s")

    ydl_opts: Dict[str, Any] = {
        "outtmpl": out_template,
        "progress_hooks": [progress_hook],
        "quiet": True,
        "no_warnings": True,
        "js_runtimes": {"node": {}},
        "windowsfilenames": True,
    }

    if fmt == "mp3":
        bitrate = "320"
        if quality in ["320k", "192k", "128k"]:
            bitrate = quality.replace("k", "")
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": bitrate,
        }]
    elif fmt == "4k":
        ydl_opts["format"] = "bestvideo[height<=2160]+bestaudio/best[height<=2160]/best"
        ydl_opts["merge_output_format"] = "mp4"
    else: # mp4
        if quality and quality.isdigit():
            h = int(quality)
            ydl_opts["format"] = f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/best"
        else:
            ydl_opts["format"] = "bestvideo+bestaudio/best"
        ydl_opts["merge_output_format"] = "mp4"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if "entries" in info and info["entries"]:
                info = info["entries"][0]
            title = info.get("title", "download")

        files = [f for f in os.listdir(task_dir) if not f.endswith(".part") and not f.endswith(".ytdl")]
        if not files:
            raise Exception("Downloaded media file could not be found")

        final_file_name = files[0]
        final_file_path = os.path.join(task_dir, final_file_name)
        file_size = os.path.getsize(final_file_path)

        with tasks_lock:
            tasks[task_id].update({
                "status": "completed",
                "percent": 100.0,
                "message": "Download complete! Saving directly to your device...",
                "filename": final_file_name,
                "file_path": final_file_path,
                "file_size": file_size,
                "file_size_str": format_bytes(file_size),
                "download_url": f"/api/file/{task_id}"
            })
            download_history.insert(0, {
                "task_id": task_id,
                "title": title,
                "filename": final_file_name,
                "format": fmt.upper(),
                "quality": quality,
                "size_str": format_bytes(file_size),
                "timestamp": int(time.time()),
                "download_url": f"/api/file/{task_id}"
            })

    except Exception as e:
        logger.error(f"Download thread error for {task_id}: {e}")
        with tasks_lock:
            tasks[task_id].update({
                "status": "error",
                "message": f"Download failed: {str(e)[:160]}"
            })

@app.post("/api/download")
def start_download(req: DownloadRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Please provide a valid video URL")

    task_id = str(uuid.uuid4())[:8]

    # If running in serverless environment without persistent disk/FFmpeg, provide instant direct CDN link
    if IS_SERVERLESS:
        try:
            ydl_opts = {"quiet": True, "skip_download": True, "js_runtimes": {"node": {}}}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if "entries" in info and info["entries"]:
                    info = info["entries"][0]
                
                title = sanitize_filename(info.get("title", "video"))
                formats = info.get("formats", [])
                chosen_url = None
                
                if req.format == "mp3":
                    for f in formats:
                        if f.get("acodec") != "none" and f.get("vcodec") == "none" and f.get("url"):
                            chosen_url = f.get("url")
                            break
                else:
                    for f in formats:
                        if req.quality.isdigit() and f.get("height") == int(req.quality) and f.get("url"):
                            chosen_url = f.get("url")
                            break
                    if not chosen_url:
                        for f in formats:
                            if f.get("vcodec") != "none" and f.get("url"):
                                chosen_url = f.get("url")
                                break

                chosen_url = chosen_url or info.get("url")
                if chosen_url:
                    ext = "mp3" if req.format == "mp3" else "mp4"
                    return {
                        "task_id": task_id,
                        "status": "completed",
                        "percent": 100.0,
                        "message": "Stream verified! Initiating direct download to your device...",
                        "direct_download": True,
                        "download_url": chosen_url,
                        "filename": f"{title}.{ext}"
                    }
        except Exception as e:
            logger.warning(f"Serverless direct extraction fallback failed: {e}")

    with tasks_lock:
        tasks[task_id] = {
            "task_id": task_id,
            "url": url,
            "format": req.format,
            "quality": req.quality,
            "status": "queued",
            "percent": 0.0,
            "speed": "0 KB/s",
            "eta": "--",
            "downloaded": "0 B",
            "total": "--",
            "message": "Queued in download engine...",
            "created_at": time.time()
        }

    thread = threading.Thread(
        target=run_download_thread,
        args=(task_id, url, req.format, req.quality),
        daemon=True
    )
    thread.start()

    return {"task_id": task_id, "status": "started"}

@app.get("/api/progress/{task_id}")
def get_progress(task_id: str):
    with tasks_lock:
        task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.get("/api/file/{task_id}")
def serve_file(task_id: str):
    with tasks_lock:
        task = tasks.get(task_id)
    if not task or task.get("status") != "completed":
        raise HTTPException(status_code=404, detail="File is not ready or does not exist")

    file_path = task.get("file_path")
    filename = task.get("filename", "video.mp4")

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    encoded_filename = urllib.parse.quote(filename)
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        "Access-Control-Expose-Headers": "Content-Disposition"
    }

    media_type = "audio/mpeg" if filename.lower().endswith(".mp3") else "video/mp4"
    return FileResponse(file_path, media_type=media_type, headers=headers, filename=filename)

@app.get("/api/thumbnail")
def proxy_thumbnail(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="Missing url parameter")
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        return Response(content=resp.content, media_type=resp.headers.get("Content-Type", "image/jpeg"))
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to load thumbnail")

@app.get("/api/history")
def get_history():
    return download_history[:30]

@app.delete("/api/history/{task_id}")
def delete_history_item(task_id: str):
    global download_history
    download_history = [item for item in download_history if item["task_id"] != task_id]
    task_dir = os.path.join(DOWNLOADS_DIR, task_id)
    if os.path.exists(task_dir):
        try:
            shutil.rmtree(task_dir, ignore_errors=True)
        except Exception:
            pass
    with tasks_lock:
        tasks.pop(task_id, None)
    return {"status": "deleted"}

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "engine": "VideoFetcher",
        "version": "2.0.0",
        "serverless": IS_SERVERLESS
    }

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

# AWS Lambda / Netlify Serverless handler
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    handler = None

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=False)
