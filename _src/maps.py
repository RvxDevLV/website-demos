"""Static map picture for a business page, made from OpenStreetMap tiles when the page is built.
No iframe and no third-party request when a visitor opens the page."""
import math, os, re, time, urllib.request

UA = "website-demos-build/1.0"  # OSM asks clients to identify themselves; no personal details go to outside services


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30).read()


def static_map(la, lo, dest, cache, z=16, W=1000, H=500, get=fetch):
    from PIL import Image, ImageOps
    n = 2 ** z
    fx, fy = (lo + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(la))) / math.pi) / 2 * n
    cx, cy = int(fx), int(fy)
    os.makedirs(cache, exist_ok=True)
    canvas = Image.new("RGB", (5 * 256, 3 * 256))
    for dx in range(-2, 3):
        for dy in range(-1, 2):
            f = os.path.join(cache, f"{z}-{cx + dx}-{cy + dy}.png")
            try:
                tile = Image.open(f); tile.load()
            except Exception:  # missing or damaged cache file: fetch again (OSM policy: go slowly, cache)
                tmp = f + ".part"
                open(tmp, "wb").write(get(f"https://tile.openstreetmap.org/{z}/{cx + dx}/{cy + dy}.png"))
                tile = Image.open(tmp); tile.load()  # raises if the download was not an image
                tile.close(); os.replace(tmp, f); tile = Image.open(f); tile.load()
                time.sleep(.4)
            canvas.paste(tile.convert("RGB"), ((dx + 2) * 256, (dy + 1) * 256))
    px, py = (2 + fx - cx) * 256, (1 + fy - cy) * 256
    g = ImageOps.autocontrast(ImageOps.grayscale(canvas.crop((round(px - W / 2), round(py - H / 2), round(px + W / 2), round(py + H / 2)))), cutoff=1)
    ImageOps.colorize(g, black="#566167", white="#fcfcfb", mid="#e0e4e3").save(dest, "WEBP", quality=80)


def finish_map(page, out, cache, get=fetch):
    """Write karte.webp next to the page. If the tiles can't be had, the page keeps its address card without a picture."""
    m = re.search(r'<div class="map" data-geo="([\d.\-]+),([\d.\-]+)">', page)
    if m:
        try:
            static_map(float(m.group(1)), float(m.group(2)), out / "karte.webp", cache, get=get)
        except Exception as ex:
            print("map not made:", ex)
            page = re.sub(r'<a class="map-img".*?</a>', "", page, count=1, flags=re.S).replace('<small class="credit">Karte © OpenStreetMap</small>', "")
    return page
