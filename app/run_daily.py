import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from images import cleanup
from news_collector import collect
from news_processor import summarize
from pdf_generator import generate_pdf

STORAGE = Path("/opt/ai-news-reader/storage")


def main():
    articles = collect(hours=72)
    if len(articles) < 15:
        raise RuntimeError(f"Only {len(articles)} articles collected, keeping the old edition")
    data = summarize(articles)
    arts = data["articles"]
    if len(arts) < 10:
        raise RuntimeError("Too few summaries returned, keeping the old edition")

    tmp = STORAGE / "daily-news.tmp.pdf"
    pages = generate_pdf(data, str(tmp))
    with open(tmp, "rb") as f:
        head = f.read(5)
    if head != b"%PDF-" or tmp.stat().st_size < 2000:
        raise RuntimeError("Generated PDF is invalid, keeping the old edition")
    os.replace(tmp, STORAGE / "daily-news.pdf")

    meta = {"generated": datetime.now().isoformat(timespec="seconds"), "count": len(arts),
            "pages": pages, "top5": data["top5"], "fact": data["fact"], "articles": arts}
    jtmp = STORAGE / "latest.tmp.json"
    jtmp.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(jtmp, STORAGE / "latest.json")
    cleanup({a["image"] for a in arts if a.get("image")})
    print(f"OK: {len(arts)} articles, {pages} pages, {sum(1 for a in arts if a.get('image'))} images")


if __name__ == "__main__":
    main()
