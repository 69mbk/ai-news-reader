import hashlib
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

IMG_DIR = Path("/opt/ai-news-reader/storage/img")
HEADERS = {"User-Agent": "Mozilla/5.0 (ai-news-reader)"}


def fetch_image(url, max_w=900):
    if not url:
        return None
    name = hashlib.sha1(url.encode()).hexdigest()[:16] + ".jpg"
    dest = IMG_DIR / name
    if dest.exists():
        return name
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        r.raise_for_status()
        if len(r.content) > 8_000_000:
            return None
        im = Image.open(BytesIO(r.content)).convert("RGB")
        if im.width < 300 or im.height < 150:
            return None
        if im.width > max_w:
            im = im.resize((max_w, int(im.height * max_w / im.width)))
        IMG_DIR.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(name + ".tmp")
        im.save(tmp, "JPEG", quality=72, optimize=True)
        tmp.replace(dest)
        return name
    except Exception as ex:
        print(f"[img] {url[:70]}: {ex}")
        return None


def cleanup(keep):
    if IMG_DIR.exists():
        for f in IMG_DIR.glob("*.jpg"):
            if f.name not in keep:
                f.unlink()
