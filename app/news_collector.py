import calendar
import html
import re
import time
from datetime import datetime, timedelta, timezone

import feedparser
import requests

FEEDS = {
    "Hespress (AR)": "https://www.hespress.com/feed",
    "Hespress (FR)": "https://fr.hespress.com/feed",
    "Hespress (EN)": "https://en.hespress.com/feed",
    "Yabiladi": "https://www.yabiladi.com/rss/articles.xml",
    "Médias24": "https://medias24.com/feed/",
    "NASA": "https://www.nasa.gov/feed/",
    "Nature": "https://www.nature.com/nature.rss",
    "Phys.org": "https://phys.org/rss-feed/",
    "Quanta Magazine": "https://api.quantamagazine.org/feed/",
    "Space.com": "https://www.space.com/feeds/all",
    "MIT Technology Review": "https://www.technologyreview.com/feed/",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
    "Hugging Face": "https://huggingface.co/blog/feed.xml",
    "Google DeepMind": "https://deepmind.google/blog/rss.xml",
    "BleepingComputer": "https://www.bleepingcomputer.com/feed/",
    "The Hacker News": "https://feeds.feedburner.com/TheHackersNews",
    "Krebs on Security": "https://krebsonsecurity.com/feed/",
    "Cloudflare Blog": "https://blog.cloudflare.com/rss/",
    "Reddit r/Morocco": "https://www.reddit.com/r/Morocco/top/.rss?t=day",
    "Reddit r/science": "https://www.reddit.com/r/science/top/.rss?t=day",
    "Reddit r/space": "https://www.reddit.com/r/space/top/.rss?t=day",
    "Reddit r/netsec": "https://www.reddit.com/r/netsec/top/.rss?t=day",
    "Reddit r/homelab": "https://www.reddit.com/r/homelab/top/.rss?t=day",
}

PER_SOURCE = 10
HEADERS = {"User-Agent": "Mozilla/5.0 (ai-news-reader)"}
IMG_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.I)
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")


def clean(text):
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def find_image(e):
    for m in e.get("media_content", []) or []:
        u = m.get("url", "")
        if u and (m.get("medium") == "image" or str(m.get("type", "")).startswith("image")
                  or u.lower().split("?")[0].endswith(IMG_EXT)):
            return u
    for m in e.get("media_thumbnail", []) or []:
        if m.get("url"):
            return m["url"]
    for enc in e.get("enclosures", []) or []:
        if str(enc.get("type", "")).startswith("image"):
            return enc.get("href") or enc.get("url")
    blobs = [e.get("summary", "")] + [c.get("value", "") for c in e.get("content", []) or []]
    for b in blobs:
        m = IMG_RE.search(b or "")
        if m and m.group(1).startswith("http"):
            return m.group(1)
    return None


def collect(hours=72):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    articles, seen = [], set()

    for source, url in FEEDS.items():
        if "reddit.com" in url:
            time.sleep(4)
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            feed = feedparser.parse(r.content)
        except Exception as ex:
            print(f"[WARN] {source}: {ex}")
            continue

        items = []
        for e in feed.entries:
            ts = e.get("published_parsed") or e.get("updated_parsed")
            if not ts:
                continue
            published = datetime.fromtimestamp(calendar.timegm(ts), timezone.utc)
            link = e.get("link", "")
            title = clean(e.get("title", ""))
            key = link or title.lower()
            if published < cutoff or key in seen or not title:
                continue
            seen.add(key)
            raw = (e.get("content") or [{}])[0].get("value") or e.get("summary", "")
            items.append({
                "title": title,
                "url": link,
                "source": source,
                "published": published.isoformat(),
                "text": clean(raw)[:1500],
                "image": find_image(e),
            })
        items.sort(key=lambda a: a["published"], reverse=True)
        articles.extend(items[:6 if source.startswith("Reddit") else PER_SOURCE])

    articles.sort(key=lambda a: a["published"], reverse=True)
    return articles


if __name__ == "__main__":
    from collections import Counter

    items = collect()
    print(f"{len(items)} articles, {sum(1 for a in items if a['image'])} with image")
    print(Counter(a["source"] for a in items))
