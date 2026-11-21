/**
 * VideoFetcher - Universal Social Media Video Downloader Client
 * Pure English, High-Performance Full Screen Web Application
 */

document.addEventListener('DOMContentLoaded', () => {
    // API Base Configuration (Supports Netlify Proxy or Remote Backend)
    const API_BASE = (window.VIDEOFETCHER_API || '').replace(/\/+$/, '');

    // Application State
    let currentVideoData = null;
    let selectedFormat = 'mp4'; // 'mp4', 'mp3', '4k'
    let selectedQuality = 'best';
    let pollInterval = null;

    // DOM Elements
    const videoUrlInput = document.getElementById('videoUrlInput');
    const pasteBtn = document.getElementById('pasteBtn');
    const clearBtn = document.getElementById('clearBtn');
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');

    const chipMp4 = document.getElementById('chipMp4');
    const chipMp3 = document.getElementById('chipMp3');
    const chip4k = document.getElementById('chip4k');
    const formatChips = [chipMp4, chipMp3, chip4k];

    const qualitySelect = document.getElementById('qualitySelect');
    const detectedCountBadge = document.getElementById('detectedCountBadge');

    const skeletonCard = document.getElementById('skeletonCard');
    const activeVideoCard = document.getElementById('activeVideoCard');
    const videoThumb = document.getElementById('videoThumb');
    const videoDuration = document.getElementById('videoDuration');
    const videoTitle = document.getElementById('videoTitle');
    const videoUploader = document.getElementById('videoUploader');
    const videoViews = document.getElementById('videoViews');
    const videoEstSize = document.getElementById('videoEstSize');
    const platformTag = document.getElementById('platformTag');
    const platformName = document.getElementById('platformName');

    const downloadBtn = document.getElementById('downloadBtn');
    const downloadBtnText = document.getElementById('downloadBtnText');

    // Modal Elements
    const progressModal = document.getElementById('progressModal');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const progressMessage = document.getElementById('progressMessage');
    const progressPercent = document.getElementById('progressPercent');
    const progressBarFill = document.getElementById('progressBarFill');
    const statSpeed = document.getElementById('statSpeed');
    const statEta = document.getElementById('statEta');
    const statSize = document.getElementById('statSize');
    const downloadCompleteActions = document.getElementById('downloadCompleteActions');
    const directDownloadLink = document.getElementById('directDownloadLink');
    const downloadAnotherBtn = document.getElementById('downloadAnotherBtn');

    // History Modal Elements
    const historyBtn = document.getElementById('historyBtn');
    const historyModal = document.getElementById('historyModal');
    const closeHistoryBtn = document.getElementById('closeHistoryBtn');
    const historyList = document.getElementById('historyList');

    const toast = document.getElementById('toast');

    // Toast Notification Helper
    function showToast(message, duration = 3500) {
        toast.textContent = message;
        toast.classList.remove('hidden');
        setTimeout(() => {
            toast.classList.add('hidden');
        }, duration);
    }

    // URL Validator
    function isValidUrl(string) {
        try {
            const url = new URL(string.startsWith('http') ? string : 'https://' + string);
            return url.hostname.length > 3 && url.hostname.includes('.');
        } catch (_) {
            return false;
        }
    }

    // Input Change & Clear Handlers
    videoUrlInput.addEventListener('input', () => {
        const val = videoUrlInput.value.trim();
        if (val) {
            clearBtn.classList.remove('hidden');
            handleUrlChange(val);
        } else {
            clearBtn.classList.add('hidden');
            resetState();
        }
    });

    clearBtn.addEventListener('click', () => {
        videoUrlInput.value = '';
        clearBtn.classList.add('hidden');
        resetState();
        videoUrlInput.focus();
    });

    // Clipboard Paste Integration
    pasteBtn.addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            if (text && text.trim()) {
                videoUrlInput.value = text.trim();
                clearBtn.classList.remove('hidden');
                showToast("Link pasted from clipboard!");
                handleUrlChange(text.trim());
            } else {
                showToast("No video link found in clipboard.");
            }
        } catch (err) {
            videoUrlInput.focus();
            showToast("Clipboard access denied. Please press Ctrl+V to paste.");
        }
    });

    // Auto-Analyze Debounce
    let debounceTimer = null;
    function handleUrlChange(rawUrl) {
        clearTimeout(debounceTimer);
        const url = rawUrl.trim();
        if (!url || !isValidUrl(url)) {
            return;
        }

        // Display instant analyzing state
        statusIndicator.classList.remove('hidden');
        statusText.textContent = "Analyzing video stream and extracting available formats...";
        skeletonCard.classList.remove('hidden');
        activeVideoCard.classList.add('hidden');
        downloadBtn.classList.add('disabled');
        downloadBtn.disabled = true;

        debounceTimer = setTimeout(() => {
            analyzeVideo(url);
        }, 400);
    }

    // Call Video Analyze Endpoint
    async function analyzeVideo(url) {
        try {
            const res = await fetch(`${API_BASE}/api/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.detail || "Failed to analyze video. Please verify the URL.");
            }

            currentVideoData = data;
            renderVideoDetails(data);
            statusIndicator.classList.add('hidden');
            showToast("Video analyzed successfully!");
        } catch (err) {
            statusIndicator.classList.add('hidden');
            showToast(err.message || "Failed to analyze video. Please try again.", 4500);
            resetState();
        }
    }

    function renderVideoDetails(data) {
        videoTitle.textContent = data.title;
        videoTitle.title = data.title;
        videoUploader.textContent = data.uploader;
        videoViews.textContent = `${data.views_str} views`;
        videoDuration.textContent = data.duration_str;

        // Platform Tag
        platformName.textContent = data.platform.name;
        platformTag.style.color = data.platform.color;
        platformTag.style.borderColor = `${data.platform.color}40`;
        platformTag.style.background = `${data.platform.color}15`;

        // Thumbnail with fallback proxy
        if (data.thumbnail) {
            videoThumb.src = `${API_BASE}/api/thumbnail?url=${encodeURIComponent(data.thumbnail)}`;
        } else {
            videoThumb.src = "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='115' fill='%231e293b'><rect width='100%' height='100%'/></svg>";
        }

        // Populate Stream Options
        populateQualityOptions();

        // Reveal Active Card
        skeletonCard.classList.add('hidden');
        activeVideoCard.classList.remove('hidden');

        // Enable Download Button
        downloadBtn.classList.remove('disabled');
        downloadBtn.disabled = false;
        downloadBtnText.textContent = `Download ${selectedFormat.toUpperCase()}`;
    }

    function populateQualityOptions() {
        if (!currentVideoData) return;

        qualitySelect.innerHTML = '';
        let options = [];

        if (selectedFormat === 'mp3') {
            options = currentVideoData.audio_options || [
                { quality: '320k', label: 'MP3 High Quality (320 kbps)', badge: 'HQ' },
                { quality: '192k', label: 'MP3 Standard (192 kbps)', badge: 'STD' },
                { quality: '128k', label: 'MP3 Compact (128 kbps)', badge: 'ECO' }
            ];
            options.forEach(opt => {
                const el = document.createElement('option');
                el.value = opt.quality;
                el.textContent = `${opt.label} • [${opt.badge}]`;
                qualitySelect.appendChild(el);
            });
            detectedCountBadge.textContent = "MP3 Audio";
            videoEstSize.textContent = "High-Quality Audio";
        } else if (selectedFormat === '4k') {
            const f4k = currentVideoData.resolutions.find(r => r.height >= 2160);
            if (f4k) {
                const el = document.createElement('option');
                el.value = '2160';
                el.textContent = `${f4k.label} • [${f4k.size_str}]`;
                qualitySelect.appendChild(el);
                videoEstSize.textContent = f4k.size_str;
                detectedCountBadge.textContent = "4K UHD Master";
            } else {
                const highest = currentVideoData.resolutions[0];
                const el = document.createElement('option');
                el.value = highest ? String(highest.height) : 'best';
                el.textContent = `${highest ? highest.label : 'Highest Available Resolution'} • [${highest ? highest.size_str : 'Auto'}]`;
                qualitySelect.appendChild(el);
                videoEstSize.textContent = highest ? highest.size_str : "Auto Size";
                detectedCountBadge.textContent = highest ? `${highest.height}p` : "Best Available";
            }
        } else {
            // MP4 Standard
            options = currentVideoData.resolutions || [];
            options.forEach(opt => {
                const el = document.createElement('option');
                el.value = String(opt.height);
                el.textContent = `${opt.label} • [${opt.size_str}]`;
                qualitySelect.appendChild(el);
            });
            detectedCountBadge.textContent = `${options.length} Qualities Available`;
            if (options[0]) {
                videoEstSize.textContent = options[0].size_str;
            }
        }

        selectedQuality = qualitySelect.value;
    }

    qualitySelect.addEventListener('change', () => {
        selectedQuality = qualitySelect.value;
        if (currentVideoData && selectedFormat === 'mp4') {
            const match = currentVideoData.resolutions.find(r => String(r.height) === selectedQuality);
            if (match) {
                videoEstSize.textContent = match.size_str;
            }
        }
    });

    // Format Chips Handler
    formatChips.forEach(chip => {
        chip.addEventListener('click', () => {
            formatChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            selectedFormat = chip.dataset.format;
            if (currentVideoData) {
                downloadBtnText.textContent = `Download ${selectedFormat.toUpperCase()}`;
            }
            populateQualityOptions();
        });
    });

    function resetState() {
        currentVideoData = null;
        skeletonCard.classList.remove('hidden');
        activeVideoCard.classList.add('hidden');
        downloadBtn.classList.add('disabled');
        downloadBtn.disabled = true;
        downloadBtnText.textContent = "Download Video";
        statusIndicator.classList.add('hidden');
    }

    // Download Button Action
    downloadBtn.addEventListener('click', async () => {
        const url = videoUrlInput.value.trim();
        if (!url || !isValidUrl(url)) {
            showToast("Please provide a valid video URL.");
            return;
        }

        startDownload(url, selectedFormat, selectedQuality);
    });

    async function startDownload(url, format, quality) {
        try {
            progressModal.classList.remove('hidden');
            downloadCompleteActions.classList.add('hidden');
            progressBarFill.style.width = '0%';
            progressPercent.textContent = '0%';
            progressMessage.textContent = "Initializing download engine...";
            statSpeed.textContent = '0 KB/s';
            statEta.textContent = '--';
            statSize.textContent = '--';

            const res = await fetch(`${API_BASE}/api/download`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, format, quality })
            });

            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.detail || "Download failed. Please try again.");
            }

            // Direct download mode (Serverless / Direct CDN link)
            if (data.direct_download && data.download_url) {
                progressBarFill.style.width = '100%';
                progressPercent.textContent = '100%';
                progressMessage.textContent = "Direct download ready! Saving to your device...";

                const directUrl = data.download_url;
                directDownloadLink.href = directUrl;
                downloadCompleteActions.classList.remove('hidden');

                triggerBrowserDownload(directUrl);
                return;
            }

            pollProgress(data.task_id);
        } catch (err) {
            progressModal.classList.add('hidden');
            showToast(err.message || "Download failed. Please try again.", 4500);
        }
    }

    function pollProgress(taskId) {
        clearInterval(pollInterval);
        pollInterval = setInterval(async () => {
            try {
                const res = await fetch(`${API_BASE}/api/progress/${taskId}`);
                if (!res.ok) {
                    clearInterval(pollInterval);
                    return;
                }

                const data = await res.json();

                const percent = Math.min(100, Math.max(0, data.percent || 0));
                progressBarFill.style.width = `${percent}%`;
                progressPercent.textContent = `${percent}%`;
                progressMessage.textContent = data.message || "Downloading stream...";
                statSpeed.textContent = data.speed || "--";
                statEta.textContent = data.eta || "--";
                statSize.textContent = `${data.downloaded || '0 B'} / ${data.total || '--'}`;

                if (data.status === 'completed') {
                    clearInterval(pollInterval);
                    progressBarFill.style.width = '100%';
                    progressPercent.textContent = '100%';
                    progressMessage.textContent = "Download complete! Saving to your device...";

                    const finalDownloadUrl = data.download_url.startsWith('http') ? data.download_url : `${API_BASE}${data.download_url}`;
                    directDownloadLink.href = finalDownloadUrl;
                    downloadCompleteActions.classList.remove('hidden');

                    triggerBrowserDownload(finalDownloadUrl);
                } else if (data.status === 'error') {
                    clearInterval(pollInterval);
                    progressMessage.textContent = data.message || "Download failed.";
                    progressBarFill.style.background = '#ef4444';
                    showToast(data.message || "Download failed.", 5000);
                }
            } catch (e) {
                console.error("Progress error:", e);
            }
        }, 650);
    }

    function triggerBrowserDownload(fileUrl) {
        const link = document.createElement('a');
        link.href = fileUrl;
        link.setAttribute('download', '');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    closeModalBtn.addEventListener('click', () => {
        clearInterval(pollInterval);
        progressModal.classList.add('hidden');
    });

    downloadAnotherBtn.addEventListener('click', () => {
        progressModal.classList.add('hidden');
        videoUrlInput.value = '';
        clearBtn.classList.add('hidden');
        resetState();
        videoUrlInput.focus();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // History Modal Handlers
    historyBtn.addEventListener('click', () => {
        historyModal.classList.remove('hidden');
        loadHistory();
    });

    closeHistoryBtn.addEventListener('click', () => {
        historyModal.classList.add('hidden');
    });

    async function loadHistory() {
        try {
            const res = await fetch(`${API_BASE}/api/history`);
            const data = await res.json();
            renderHistory(data);
        } catch (e) {
            console.error("History fetch error:", e);
        }
    }

    function renderHistory(items) {
        historyList.innerHTML = '';
        if (!items || items.length === 0) {
            historyList.innerHTML = `<p class="empty-notice">No downloads recorded yet.</p>`;
            return;
        }

        items.forEach(item => {
            const el = document.createElement('div');
            el.className = 'history-entry';
            const dlUrl = item.download_url.startsWith('http') ? item.download_url : `${API_BASE}${item.download_url}`;
            el.innerHTML = `
                <div class="history-left">
                    <div class="h-title" title="${item.title}">${item.title}</div>
                    <div class="h-meta">
                        <span>Format: ${item.format}</span>
                        <span>•</span>
                        <span>Size: ${item.size_str}</span>
                    </div>
                </div>
                <div class="history-right">
                    <a href="${dlUrl}" class="h-dl-btn" download>Download</a>
                    <button class="h-del-btn" data-id="${item.task_id}" title="Remove from list">✕</button>
                </div>
            `;

            el.querySelector('.h-del-btn').addEventListener('click', async (e) => {
                const id = e.target.dataset.id;
                await fetch(`${API_BASE}/api/history/${id}`, { method: 'DELETE' });
                loadHistory();
            });

            historyList.appendChild(el);
        });
    }

    // Mobile Navigation Menu Toggle
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navLinks = document.getElementById('navLinks');
    if (mobileMenuBtn && navLinks) {
        mobileMenuBtn.addEventListener('click', () => {
            navLinks.classList.toggle('mobile-open');
            mobileMenuBtn.classList.toggle('active');
        });
        navLinks.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('mobile-open');
                mobileMenuBtn.classList.remove('active');
            });
        });
    }
});
