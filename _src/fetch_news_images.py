"""Download the lead image (og:image / twitter:image) of each news source and store it as the cover.
Usage:  python _src/fetch_news_images.py [slug ...]   (no args = every news item not yet done)
Writes assets/img/news/<slug>.jpg (1200x630 centre crop) and records credit in _src/news_images.json.
Falls back silently (keeps the drawn cover) when the source has no usable image.
"""
import io
import json
import os
import re
import sys
from urllib.parse import urljoin

import requests
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from news_data import NEWS  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "assets", "img", "news")
REG = os.path.join(os.path.dirname(__file__), "news_images.json")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}


# Pages without og:image: use the article's own lead image.
OVERRIDE = {
    "nsf-fabaid-data-fabric": "https://computing.unl.edu/sites/unl.edu.engineering.school-of-computing/files/media/image/hcc.jpg",
}


def find_image(page_url, html):
    pats = [
        r'<meta[^>]+property=["\']og:image(?::secure_url)?["\'][^>]*content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image(?::src)?["\'][^>]*content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*name=["\']twitter:image["\']',
    ]
    for p in pats:
        m = re.search(p, html, re.I)
        if m:
            return urljoin(page_url, m.group(1).replace("&amp;", "&"))
    return None


def to_cover(data, dest):
    im = Image.open(io.BytesIO(data))
    im = im.convert("RGB")
    w, h = im.size
    if w < 600 or h < 300:
        raise ValueError(f"too small {w}x{h}")
    target = 1200 / 630
    if w / h > target:
        nw = int(h * target)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / target)
        top = max(0, int((h - nh) * 0.3))  # keep a bit more of the upper part
        im = im.crop((0, top, w, top + nh))
    im = im.resize((1200, 630), Image.LANCZOS)
    im.save(dest, "JPEG", quality=84, optimize=True)
    return (w, h)


def main(only):
    reg = json.load(open(REG, encoding="utf-8")) if os.path.exists(REG) else {}
    for n in NEWS:
        slug = n["slug"]
        if only and slug not in only:
            continue
        if not only and slug in reg:
            continue
        try:
            r = requests.get(n["url"], headers=UA, timeout=25)
            r.raise_for_status()
            img = OVERRIDE.get(slug) or find_image(r.url, r.text)
            if not img:
                print(slug, "NO og:image")
                continue
            ir = requests.get(img, headers={**UA, "Referer": n["url"]}, timeout=30)
            ir.raise_for_status()
            size = to_cover(ir.content, os.path.join(OUT, slug + ".jpg"))
            reg[slug] = {"credit": n["src"], "image_url": img, "orig_size": list(size)}
            print(slug, "OK", size, img[:90])
        except Exception as e:  # noqa: BLE001
            print(slug, "FAIL", type(e).__name__, str(e)[:100])
    json.dump(reg, open(REG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(set(sys.argv[1:]))
