@echo off
title VideoFetcher - Social Media Video Downloader
cd /d "%~dp0"

echo ========================================================
echo       VideoFetcher - Social Media Video Downloader
echo ========================================================
echo.
echo Starting VideoFetcher...
echo.

python run.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Server stopped or an error occurred.
    pause
)
