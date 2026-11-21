<div align="center">

# 🎬 VideoFetcher

### Universal High-Speed Social Media Video & Audio Downloader

[![Netlify Status](https://api.netlify.com/api/v1/badges/deploy-status?branch=main)](https://app.netlify.com)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![yt-dlp](https://img.shields.io/badge/Engine-yt--dlp-red?style=for-the-badge)](https://github.com/yt-dlp/yt-dlp)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-555555?style=for-the-badge&logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

<br/>

**VideoFetcher** is a full-screen, responsive web application engineered to download social media videos and audio in seconds. Paste any link—it automatically analyzes metadata, stream resolutions (from **360p up to 4K Ultra HD**), and high-fidelity **320kbps MP3 audio**, saving directly to the user's device with zero watermarks.

<br/>

[![Deploy to Netlify](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy)
&nbsp;&nbsp;&nbsp;&nbsp;
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

</div>

---

## ⚡ Highlights & Features

- ⚡ **Instant Auto-Analyze:** Automatically decodes stream formats and video metadata on link paste—no extra search click needed.
- 📺 **Up to 4K Ultra HD:** Native support for 2160p (4K), 1440p (2K), 1080p (Full HD), 720p (HD), 480p, and 360p.
- 🎵 **Crystal MP3 Audio (320kbps):** Extracts pristine audio tracks from music videos, podcasts, and interviews.
- 📱 **100% Responsive for All Devices:** Fluid layout tailored for iPhone, iPad, Android, laptops, tablets, and 4K ultra-wide monitors.
- 🛡️ **Zero Watermarks & 100% Free:** Unlimited downloads with no watermarks, ads, or subscriptions.
- 🌐 **1,000+ Platforms Supported:** Works with YouTube, Facebook, Instagram, TikTok, X (Twitter), Reddit, Vimeo, Pinterest, SoundCloud, and more.
- 📊 **Real-time Download Engine:** Live download percentage, speed metrics (MB/s), ETA countdown, and FFmpeg stream merging.
- ☁️ **Cloud & Serverless Ready:** Deployable to Netlify in minutes with built-in CORS, edge caching, and reverse proxying.

---

## 🌐 Supported Social Media Platforms

| Platform | Supported Formats | Features |
| :--- | :--- | :--- |
| **YouTube** | MP4 (4K, 1440p, 1080p, 720p, 480p), MP3 (320k) | Shorts, regular videos, live recordings |
| **Facebook** | HD, SD, MP3 | Facebook Watch, Reels, public feed videos |
| **Instagram** | MP4 (1080p), MP3 | Reels, video posts, Stories, IGTV |
| **TikTok** | Full HD MP4, MP3 | Watermark-free downloads |
| **X / Twitter** | MP4 (Multi-bitrate), GIF | High-definition media tweets |
| **Reddit** | MP4 with merged audio | Complete video and sound synchronization |
| **Pinterest** | MP4, Pins | Video pins in native quality |
| **Vimeo** | Up to 4K Ultra HD | Master resolution video streams |

---

## 🚀 Deployment Guide: Deploy to Netlify

VideoFetcher is configured for smooth deployment on **Netlify**.

### 🌟 Architecture Overview

```
[ User Browser / Mobile Phone ]
               │
               ▼
   [ Netlify Edge CDN (Static Frontend) ]
         ├── index.html
         ├── style.css
         └── app.js
               │
      ┌────────┴──────────────────────────┐
      ▼                                   ▼
[ Option A: Netlify Functions ]   [ Option B: Dedicated Backend (Render / Docker) ]
  • Serverless Python              • Full FFmpeg 4K Merging & MP3 Transcoding
  • Direct CDN Stream Downloads    • Continuous Background Workers
  • Zero Server Maintenance        • Unlimited File Sizes
```

---

### Option A: 1-Click Serverless Deploy on Netlify

Use Netlify's built-in serverless functions for zero-maintenance deployment:

1. **Fork or push this repository** to your GitHub/GitLab account.
2. Log in to [Netlify](https://app.netlify.com/) and click **"Add new site"** → **"Import an existing project"**.
3. Select your repository.
4. Netlify will automatically detect [`netlify.toml`](file:///d:/Project/video%20downloader/netlify.toml):
   - **Publish directory:** `static`
   - **Functions directory:** `netlify/functions`
5. Click **"Deploy VideoFetcher"**.
6. Your website is immediately live at `https://your-site-name.netlify.app`! 🎉

---

### Option B: Netlify Frontend + Free Render Backend (Recommended for 4K & FFmpeg)

For maximum performance (handling 4K DASH video merging and MP3 encoding), deploy the backend on Render's free tier and connect it to your Netlify frontend:

#### Step 1: Deploy Backend to Render (Free)
1. Click the **Deploy to Render** button or link your repo to [Render](https://render.com/).
2. Select **Web Service** and choose **Docker** runtime (or Python with [`render.yaml`](file:///d:/Project/video%20downloader/render.yaml)).
3. Render will deploy your container with `ffmpeg`, `nodejs`, and `yt-dlp` pre-installed.
4. Copy your backend URL (e.g. `https://videofetcher-backend.onrender.com`).

#### Step 2: Connect to Netlify
In your [`netlify.toml`](file:///d:/Project/video%20downloader/netlify.toml), point the redirect rule to your Render backend:
```toml
[[redirects]]
  from = "/api/*"
  to = "https://videofetcher-backend.onrender.com/api/:splat"
  status = 200
  force = true
```
Push the commit. Netlify will now transparently proxy all API requests to your dedicated backend with **zero CORS issues**!

---

## 💻 Local Development & Quick Start

### Prerequisites
- **Python 3.10+** (Tested on Python 3.12)
- **FFmpeg** (Installed and in system PATH)
- **Node.js** (Optional, recommended for YouTube extraction runtime)

### 1-Click Launch (Windows)
Double-click:
```bat
start.bat
```

### Command Line Launch
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/videofetcher.git
   cd videofetcher
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the development server:
   ```bash
   python run.py
   ```
4. Access the web app:
   - 💻 **On your PC:** `http://localhost:5000`
   - 📱 **On your Phone (Same Wi-Fi):** `http://<your-local-ip>:5000`

---

## 🐳 Docker Deployment

Run VideoFetcher anywhere using Docker:

```bash
# Build the Docker image
docker build -t videofetcher .

# Run the container on port 5000
docker run -d -p 5000:5000 --name videofetcher-app videofetcher
```
Visit `http://localhost:5000` in your browser.

---

## 📂 Project Structure

```text
├── netlify.toml               # Netlify build, redirect, and caching configuration
├── Dockerfile                 # Multi-stage production container with FFmpeg
├── render.yaml                # 1-Click deployment blueprint for Render
├── requirements.txt           # Python dependencies (FastAPI, yt-dlp, Mangum)
├── server.py                  # Core FastAPI backend & serverless handler
├── run.py                     # Local launcher with network IP detection
├── start.bat                  # 1-Click Windows execution script
│
├── netlify/
│   └── functions/
│       ├── api.py             # Netlify Serverless Python function entry point
│       └── requirements.txt   # Lambda/Serverless requirements
│
├── static/
│   ├── _redirects             # Netlify SPA & API proxy fallback rules
│   ├── index.html             # Full-screen responsive web UI
│   ├── style.css              # Glassmorphism, animations & mobile CSS
│   └── app.js                 # Auto-analyze engine, progress & download logic
│
└── downloads/                 # Temporary media processing directory (auto-cleaned)
```

---

## 📡 REST API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/analyze` | `POST` | Analyzes a video URL and returns metadata, stream formats, and resolutions. |
| `/api/download` | `POST` | Initiates background stream download and conversion task. |
| `/api/progress/{task_id}` | `GET` | Fetches live progress percentage, speed (MB/s), and ETA. |
| `/api/file/{task_id}` | `GET` | Streams the finished video/audio file with `Content-Disposition`. |
| `/api/thumbnail` | `GET` | Proxies video thumbnails to prevent CORS and hotlinking restrictions. |
| `/api/history` | `GET` | Retrieves the list of recently completed downloads. |
| `/api/health` | `GET` | Health-check endpoint for container monitoring. |

---

## 🔒 Security & Fair Use

- **Data Privacy:** VideoFetcher does not store user data or track browsing history. Media files are automatically cleaned up from temporary storage.
- **Fair Use Notice:** VideoFetcher is intended for personal backup, offline viewing, and educational fair use. Please respect copyright laws and terms of service of respective content platforms.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
Feel free to star ⭐ the repository if you found it helpful!
