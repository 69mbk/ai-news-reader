# AI Daily News Reader

Self-hosted daily news magazine. A Python backend on a Proxmox LXC collects RSS feeds (Morocco, science, AI, cybersecurity), summarizes and translates them to French with the Gemini API, builds a magazine-style PDF, and serves everything through a FastAPI API and a mobile web page.

## Stack
Python, FastAPI, feedparser, ReportLab, Pillow, Gemini API, cron, systemd, Proxmox LXC, Tailscale.

## Setup
1. `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in your values.
3. Test: `python app/run_daily.py`
4. Run the API with uvicorn (see `main.py`), and schedule `run_daily.py` with cron.

<img width="774" height="739" alt="image" src="https://github.com/user-attachments/assets/6ec43884-52a8-4a78-a172-5be6a7952aab" />
<img width="747" height="724" alt="image" src="https://github.com/user-attachments/assets/edb1c13c-ab21-4075-8200-4d2c5706a4cb" />
AI Daily News Reader is a self-hosted automation project that produces a personalized daily news magazine. A Python backend running in a Debian LXC container on a Proxmox home server collects articles every morning from about 20 RSS sources: Moroccan news (Hespress, Yabiladi, Médias24), science (NASA, Nature, Phys.org, Quanta, Space.com), AI, and cybersecurity. The Gemini API selects the most important stories, translates Arabic and English into French, and writes summaries at three levels: a cover story, feature stories, and one-line briefs. The result is a magazine-style PDF of about 5 pages with pictures, sections, and links to the original articles. A FastAPI service with token authentication serves the edition to a mobile web page that can be installed on the phone’s home screen. Tailscale gives secure remote access without opening any router port.

Key features:

Scheduled at 07:00 with cron, plus a catch-up run if the server was off
Safe replacement: a new PDF replaces the old one only if it is valid
AI summaries limited to the source text, with real URLs always taken from the original articles
Image download and resizing, with automatic cleanup of old images
Token authentication, secrets kept in .env, nothing exposed to the internet

Architecture:
RSS feeds → collector → Gemini API → PDF generator (ReportLab) → FastAPI → phone web page, secured with Tailscale.
