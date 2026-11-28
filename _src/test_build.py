"""Checks the built demos. Run: python _src/test_build.py
1. every published page keeps its sample marks (noindex for business demos, indexable for the eight generic samples, sample note) and has no leftover {{placeholder}}
2. (needs privats/) every business demo builds in 3 variants that really differ, and shows its real phone number
Step 2 builds into privats/preview/, nothing is published."""
import json, pathlib, re, runpy, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRIV = ROOT / "privats"
GENERIC = {"autoserviss", "buvfirma", "ziedu-salons", "kafejnica", "zobarstnieciba", "frizetava", "veterinara-klinika", "apbedisanas-birojs"}
KEEP_LOOK = {"autoserviss", "bergs-serviss", "rem-sport"}  # same list as build.py: these ignore variants

for p in sorted(ROOT.glob("*/index.html")):
    h = p.read_text(encoding="utf-8")
    if p.parent.name in GENERIC:  # the eight public samples are indexed and say where they live
        assert "noindex" not in h and f'rel="canonical" href="https://rvxdevlv.github.io/website-demos/{p.parent.name}/"' in h, f"{p.parent.name}: should be indexable with a canonical"
    else:
        assert 'name="robots" content="noindex"' in h, f"{p.parent.name}: noindex missing"
    assert "demo-note" in h, f"{p.parent.name}: sample note missing"
    assert 'id="sent" role="status"' in h, f"{p.parent.name}: the form's result message must be announced to screen readers (role=status)"
    assert "{{" not in h, f"{p.parent.name}: placeholder left"

# 3. every page (also the portfolio and the privacy page): robots meta, a policy that lists exactly the inline scripts the page has
sys.path.insert(0, str(ROOT / "_src"))
from security import INLINE, script_hash
for p in [ROOT / "index.html", ROOT / "privatums.html", *sorted(ROOT.glob("*/index.html"))]:
    h, name = p.read_text(encoding="utf-8"), p.relative_to(ROOT).as_posix()
    robots = re.search(r'<meta name="robots" content="([^"]*)"', h)
    assert robots, f"{name}: robots meta missing"
    want = "index" if name == "index.html" or p.parent.name in GENERIC else "noindex"  # portfolio and the eight samples are indexed, the rest is not
    assert robots.group(1).startswith(want), f"{name}: robots is {robots.group(1)!r}, expected {want}"
    csp = re.search(r'http-equiv="Content-Security-Policy" content="([^"]*)"', h)
    assert csp, f"{name}: Content-Security-Policy missing, run python _src/security.py {name}"
    for s in INLINE.findall(h):
        assert script_hash(s) in csp.group(1), f"{name}: an inline script changed, run python _src/security.py {name}"
    assert 'name="referrer"' in h, f"{name}: referrer policy missing"

if PRIV.is_dir():
    mine = [s[0] for s in runpy.run_path(str(PRIV / "shops.py"))["SHOPS"] if (ROOT / s[0] / "index.html").exists() and s[0] not in KEEP_LOOK]
    subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "_src" / "build.py"), "--preview", "--variants", "3", *mine], check=True)  # no capture: a failed build shows its own error
    info = json.loads((PRIV / "info.json").read_text(encoding="utf-8-sig"))
    for s in mine:
        pages = [(PRIV / "preview" / (s if i == 0 else f"{s}-{i + 1}") / "index.html").read_text(encoding="utf-8") for i in range(3)]
        assert len(set(pages)) == 3, f"{s}: variants are identical"
        tel = info.get(s, {}).get("tel")
        for h in pages:
            assert "{{" not in h, f"{s}: placeholder left in a variant"
            assert not tel or tel[-8:] in re.sub(r"\D", "", h), f"{s}: real phone number missing"
print("ok:", len(list(ROOT.glob("*/index.html"))), "pages checked,", len(mine) if PRIV.is_dir() else 0, "business demos x 3 variants")
