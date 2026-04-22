# RAMA AI OS v5.0 — Advanced Features & Windows Guide

## 🪟 Windows-First Setup (Recommended for Mumbai)

### Prerequisites for Windows
```powershell
# Check versions
python --version          # 3.11+ required
node --version           # 20+ required
docker --version         # for full deployment

# Install dependencies (run as Administrator)
pip install --upgrade pip
pip install pyautogui pytesseract pillow
```

### One-Command Windows Setup
```batch
# PowerShell or CMD (as Administrator)
cd RAMA-AI
setup.bat
```

This will:
1. Check Python 3.11+ and Node 20+
2. Install all 60+ dependencies
3. Pull Ollama models (if installed)
4. Create data directories
5. Set up .env file

### Start RAMA (Windows)
```batch
start.bat
```

Auto-opens at **http://localhost:8080**

---

## 🔥 Advanced Features (Windows Compatible)

### 1. **Ghost Coder** — Autonomous PR Bot
- **What:** Watches your GitHub repo, finds issues, auto-generates fixes, opens PRs
- **Setup:**
  ```
  Set GITHUB_TOKEN in .env
  GITHUB_TOKEN=ghp_xxxxxxxxxxxx
  ```
- **Usage:**
  ```
  RAMA, activate Ghost Coder on my repo — owner/repo
  ```
- **How it works:**
  - Fetches open issues from GitHub API
  - Uses Gemini to generate fixes
  - Creates branches + opens PRs automatically
  - Runs nightly by default

---

### 2. **Viral Empire** — YouTube Shorts Creator
- **What:** Finds trending topics → generates viral scripts → builds videos → uploads
- **Requirements:**
  ```
  ffmpeg (for video generation)
  YouTube API key (for auto-upload)
  ```
- **Install FFmpeg on Windows:**
  ```powershell
  # Option 1: Chocolatey
  choco install ffmpeg
  
  # Option 2: Download from https://ffmpeg.org/download.html
  # Add to PATH: C:\ffmpeg\bin
  ```
- **Usage:**
  ```
  RAMA, start Viral Empire — find trending topics and generate 3 video scripts
  ```
- **Output:**
  - Videos saved to `data/viral_content/`
  - Queued for upload to YouTube/Instagram

---

### 3. **Bounty Hunter** — Freelance Job Finder
- **What:** Scrapes Upwork, Freelancer, Toptal; auto-generates proposals; suggests bids
- **Usage:**
  ```
  RAMA, activate Bounty Hunter — find Python API gigs on Upwork
  ```
- **Features:**
  - Monitors job feeds for keywords
  - AI-generated proposals
  - Auto-bid suggestions
  - Notification on new matches

---

### 4. **Oracle SaaS** — Startup Idea Generator
- **What:** Detects viral trends → brainstorms SaaS products → suggests what to build
- **Usage:**
  ```
  RAMA, run Oracle SaaS — what products should we build this week?
  ```
- **Output:**
  - Top trending topics
  - 3–5 SaaS product ideas
  - MVP features list
  - Revenue model suggestions
  - Build time estimates

---

### 5. **Windows Bridge** — Native OS Integration
**Unique to Windows!**
- **Clipboard Monitoring**
  ```python
  text = await win_bridge.get_clipboard()
  await win_bridge.set_clipboard("new text")
  await win_bridge.monitor_clipboard(callback)
  ```
- **Screen Recording**
  ```python
  win_bridge.record_screen("output.mp4", duration_sec=30)  # 30-second video
  ```
- **Screenshots with OCR**
  ```python
  path = win_bridge.screenshot()
  text = win_bridge.extract_text(path)  # Read all text from screen
  ```
- **Windows Notifications**
  ```python
  win_bridge.notify("RAMA Alert", "Task completed!", icon="success")
  ```
- **Process Management**
  ```python
  apps = win_bridge.get_running_apps()
  win_bridge.kill_process(pid)
  ```
- **PowerShell Integration**
  ```python
  stdout, stderr = win_bridge.powershell("Get-Service")
  ```
- **Create Shortcuts**
  ```python
  win_bridge.create_shortcut(
    target="C:\\Python311\\python.exe",
    shortcut_path="C:\\Users\\Boss\\Desktop\\RAMA.lnk",
    args="start_rama.py"
  )
  ```

---

### 6. **Chronos Debugger** — Time-Travel Debugging
- **What:** Takes memory snapshots every 10s; rewinds on crash; auto-generates patches
- **How it works:**
  1. Captures application state every 10 seconds
  2. On crash: rewinds to last stable state
  3. Analyzes error with Gemini
  4. Proposes defensive code patch
  5. Saves crash report for analysis
- **Crash reports:** `data/chronos_snapshots/`

---

### 7. **Genesis Protocol** — Self-Optimizing Code
- **What:** Profiles execution time → identifies slow functions → rewrites as faster Python or Rust
- **Usage:**
  ```
  RAMA, run genesis evolution — optimize slow modules
  ```
- **How it works:**
  - Measures latency of all functions
  - Flags anything >300ms
  - Generates optimized version
  - Can compile to Rust for 10× speedup
  - Hot-swaps the implementation

---

### 8. **OSINT Vision** — Intelligence Gathering
- **What:** Scrapes Reddit, GitHub trending, Hacker News; analyzes repos
- **Usage:**
  ```
  RAMA, run OSINT scan — what's hot on GitHub and HN?
  ```
- **Features:**
  - Reddit API (subreddits, trending posts)
  - GitHub trending (language-specific)
  - Hacker News top stories
  - Repo README analysis
  - Tech stack detection

---

### 9. **Screen Reader** — Vision-Based Automation
- **What:** Takes screenshots → OCR text extraction → visual analysis
- **Usage:**
  ```
  RAMA, read my screen and tell me what's there
  ```
- **Capabilities:**
  - Screenshot capture
  - Tesseract OCR (extracts all text)
  - Gemini vision analysis (layout, UI, actions)
  - Finds clickable elements
  - Detects screen changes

---

### 10. **File Watcher** — Auto-Trigger Workflows
- **What:** Monitors directories; triggers actions on file create/modify/delete
- **Example:**
  ```python
  watcher = FileWatcher()
  watcher.watch("/path/to/project", auto_git_commit)
  asyncio.create_task(watcher.monitor_loop())
  ```
- **Use cases:**
  - Auto-commit on code change
  - Trigger tests when test file changes
  - Backup on file creation
  - Notify on suspicious deletions

---

### 11. **ADB Bridge** — Android Phone Control
- **What:** Controls Android devices over USB/WiFi
- **Setup:**
  ```
  Enable USB Debugging on your phone
  Connect via: adb connect <IP>:5555
  ```
- **Capabilities:**
  - Take screenshots
  - Read notifications
  - Send WhatsApp messages
  - Tap, swipe, type
  - Launch/kill apps
  - Install APKs

---

### 12. **Telemetry Monitor** — System Health
- **What:** Real-time CPU, RAM, GPU, temps, network monitoring
- **Features:**
  - CPU usage %, cores, frequency
  - RAM total/used/percent
  - Disk usage
  - Network I/O
  - GPU memory (NVIDIA via nvidia-smi)
  - Temperature sensors
  - Alert levels: NOMINAL / WARNING / CRITICAL

---

## 🎯 Usage Patterns

### CEO Mode (Multi-Agent Delegation)
```
RAMA, [Task] - High Efficiency Mode. Deploy Agents.
```
Example:
```
RAMA, analyse competitor market trends and suggest 3 new features - High Efficiency Mode. Deploy Agents.
```

### Wake Words
Say or type: **RAMA**, **Buddy**, **Boss**

### Fast Commands
```
RAMA, learn from https://github.com/owner/repo
RAMA, scrape GitHub trending Python repos
RAMA, find freelance Python API gigs
RAMA, what SaaS should we build this week?
RAMA, optimize slow code
RAMA, take a screenshot and read it
```

---

## 🚀 Production Checklist (Windows)

- [ ] **Install Ollama** → Download from https://ollama.com
  ```bash
  ollama pull llama3 phi3 qwen2.5-coder llava
  ```
- [ ] **Add API keys to .env**
  ```
  GEMINI_API_KEY=your_key
  GITHUB_TOKEN=ghp_xxx (optional)
  ```
- [ ] **Install FFmpeg** (for Viral Empire)
  ```
  choco install ffmpeg
  ```
- [ ] **Install Tesseract** (for OCR)
  ```
  choco install tesseract
  ```
- [ ] **Enable USB Debugging** on Android (for ADB)
- [ ] **Test backend** → `http://localhost:3500/docs`
- [ ] **Test frontend** → `http://localhost:8080`
- [ ] **Enable Network Sentinel** → Monitor ports for threats
- [ ] **Configure Ollama GPU** → Set `OLLAMA_GPU_ACCELERATION=cuda` (or `metal`)

---

## 📊 Performance Tuning (Windows)

### For Low-Spec Hardware
```env
OLLAMA_NUM_GPUS=0          # Use CPU only
OLLAMA_MEMORY_STRATEGY=STATIC
LLAMA_QUANTIZE=q4_0        # Smaller models
```

### For High-Spec Gaming PCs
```env
OLLAMA_NUM_GPUS=2          # Use both GPUs
OLLAMA_GPU_ACCELERATION=cuda
OLLAMA_MEMORY_STRATEGY=DYNAMIC
```

### Memory Management
- FAISS vectors: incremental indexing (never > 1000 interactions)
- Telemetry history: rolling window (last 120 snapshots only)
- Chronos snapshots: max 30, auto-prune oldest

---

## 🐛 Troubleshooting (Windows)

### "Python not found"
```powershell
# Check installation
python --version

# Add to PATH if needed
$env:Path += ";C:\Python311"
```

### "Port 3500 already in use"
```powershell
# Find process using port
netstat -ano | findstr :3500

# Kill it
taskkill /PID <PID> /F

# Or use different port
set PORT=3501
```

### "Ollama models not found"
```bash
ollama list          # Check installed models
ollama pull llama3   # Download specific model
```

### "Tesseract not found" (OCR)
```powershell
choco install tesseract
# Then add to PATH or set in .env:
# PYTESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### "FFmpeg not working"
```powershell
ffmpeg -version    # Check installation
where ffmpeg       # Check PATH
```

---

## 📈 Next Steps

1. **Run setup.bat** (5 min)
2. **Edit .env** with your Gemini API key
3. **Start RAMA** with start.bat
4. **Ask a directive:**
   ```
   RAMA, what can you do for me?
   RAMA, find trending startup ideas
   RAMA, activate Bounty Hunter
   ```
5. **Enable advanced features** as needed (GitHub token, YouTube API, etc.)

---

**RAMA is ready. Boss, the future is yours. 🚀**
