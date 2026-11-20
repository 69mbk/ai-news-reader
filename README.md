# AI Daily News Reader

Self-hosted daily news magazine. A Python backend on a Proxmox LXC collects RSS feeds (Morocco, science, AI, cybersecurity), summarizes and translates them to French with the Gemini API, builds a magazine-style PDF, and serves everything through a FastAPI API and a mobile web page.

## Stack
Python, FastAPI, feedparser, ReportLab, Pillow, Gemini API, cron, systemd, Proxmox LXC, Tailscale.

## Setup
1. `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in your values.
3. Test: `python app/run_daily.py`
4. Run the API with uvicorn (see `main.py`), and schedule `run_daily.py` with cron.
