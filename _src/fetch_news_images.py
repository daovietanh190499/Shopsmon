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
    # Lead image shown on the source article (the VentureBeat/OpenAI pages block scripts).
    "openai-gpt-6-cyber": "https://images.indianexpress.com/2026/10/OpenAI-resumes-training-AI.jpg",
    "nordic-sub-ghz-edge-ai": "https://nos-p-001.sitecorecontenthub.cloud/api/public/content/4347855092e84727adda91c32ec71f75?v=605bd076",
    "qualcomm-spacex-starlink-mobile-5g": "https://s7d1.scene7.com/is/image/dmqualcommprod/SpaceXAnnouncement",
    "atsign-edgeai": "https://cdn.prod.website-files.com/6a0e0dacd9a0567a4e90580e/6ac3cad5b0b9f389d4e0e765_Intel%20x%20Atsign.webp",
    "nsf-fabaid-data-fabric": "https://computing.unl.edu/sites/unl.edu.engineering.school-of-computing/files/media/image/hcc.jpg",
    # Source page blocks scripts (403/DNS): use the lead image of another outlet covering the same event.
    "brainchip-akd1500-raspberry-pi-5": "https://www.cnx-software.com/wp-content/uploads/2026/11/Brainchip-AKD1500-Raspberry-Pi-5-Dev-Kit.jpg",
    "nordic-nrf71-edge-ai": "https://circuitdigest.com/sites/default/files/circuitdigest_news_images/nordics-new-nrf71-chip-claims-20x-lower-wi-fi-standby-power-and-adds-an-npu-for-edge-ai.jpg",
    # The press-release page only exposes the site logo; use the product visual from Infineon's own AURIX RC1 pages.
    "infineon-aurix-rc1-risc-v": "https://assets.infineon.com/is/image/infineon/aurix-rc1-visual-hi-res.jpg",
    # Press-release mirror has only a site logo; use the module image from the manufacturer's product page.
    "u-blox-sam-m11n-gnss": "https://content.u-blox.com/sites/default/files/2026-06/SAM-M11N-top-bottom.png",
    # Business Wire blocks scripts (403): product image from Quectel's own release on PR Newswire Asia.
    "quectel-sp900bf-ap-edge-ai": "https://mmx.prnasia.com/media/MS2032716/20261111052431EST_image_1.jpg?id=OA3072233&p=original",
}
# Credit for OVERRIDE images that come from a different outlet than the news source.
CREDIT_OVERRIDE = {
    "openai-gpt-6-cyber": "Reuters / The Indian Express",
    "qualcomm-spacex-starlink-mobile-5g": "Qualcomm",
    "brainchip-akd1500-raspberry-pi-5": "CNX Software",
    "nordic-nrf71-edge-ai": "CircuitDigest",
    "infineon-aurix-rc1-risc-v": "Infineon",
    "u-blox-sam-m11n-gnss": "u-blox",
    "quectel-sp900bf-ap-edge-ai": "Quectel / PR Newswire Asia",
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
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        white = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(white, im)  # transparent product shots: white background, not black
    im = im.convert("RGB")
    w, h = im.size
    if w < 480 or h < 300:
        raise ValueError(f"too small {w}x{h}")
    target = 1200 / 630
    if w < 600 or w / h < 1.25:
        # Small or near-square official image: show it whole, scaled to the cover height, over a blurred copy of itself.
        from PIL import ImageFilter
        bg = im.resize((1200, 630), Image.LANCZOS).filter(ImageFilter.GaussianBlur(28))
        fh = 630
        fw = int(w * fh / h)
        fg = im.resize((fw, fh), Image.LANCZOS)
        bg.paste(fg, ((1200 - fw) // 2, 0))
        bg.save(dest, "JPEG", quality=84, optimize=True)
        return (w, h)
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
            img = OVERRIDE.get(slug)
            if not img:
                r = requests.get(n["url"], headers=UA, timeout=25)
                r.raise_for_status()
                img = find_image(r.url, r.text)
            if not img:
                print(slug, "NO og:image")
                continue
            ir = requests.get(img, headers={**UA, "Referer": n["url"]}, timeout=30)
            ir.raise_for_status()
            size = to_cover(ir.content, os.path.join(OUT, slug + ".jpg"))
            reg[slug] = {"credit": CREDIT_OVERRIDE.get(slug, n["src"]), "image_url": img, "orig_size": list(size)}
            print(slug, "OK", size, img[:90])
        except Exception as e:  # noqa: BLE001
            print(slug, "FAIL", type(e).__name__, str(e)[:100])
    json.dump(reg, open(REG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(set(sys.argv[1:]))
