"""Checks the built demos. Run: python _src/test_build.py
1. every published page keeps its sample marks (noindex, sample note) and has no leftover {{placeholder}}
2. (needs privats/) every business demo builds in 3 variants that really differ, and shows its real phone number
Step 2 builds into privats/preview/, nothing is published."""
import json, pathlib, re, runpy, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRIV = ROOT / "privats"
KEEP_LOOK = {"autoserviss", "bergs-serviss", "rem-sport"}  # same list as build.py: these ignore variants

for p in sorted(ROOT.glob("*/index.html")):
    h = p.read_text(encoding="utf-8")
    assert 'name="robots" content="noindex"' in h, f"{p.parent.name}: noindex missing"
    assert "demo-note" in h, f"{p.parent.name}: sample note missing"
    assert "{{" not in h, f"{p.parent.name}: placeholder left"

if PRIV.is_dir():
    mine = [s[0] for s in runpy.run_path(str(PRIV / "shops.py"))["SHOPS"] if (ROOT / s[0] / "index.html").exists() and s[0] not in KEEP_LOOK]
    subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "_src" / "build.py"), "--preview", "--variants", "3", *mine], check=True, capture_output=True)
    info = json.loads((PRIV / "info.json").read_text(encoding="utf-8-sig"))
    for s in mine:
        pages = [(PRIV / "preview" / (s if i == 0 else f"{s}-{i + 1}") / "index.html").read_text(encoding="utf-8") for i in range(3)]
        assert len(set(pages)) == 3, f"{s}: variants are identical"
        tel = info.get(s, {}).get("tel")
        for h in pages:
            assert "{{" not in h, f"{s}: placeholder left in a variant"
            assert not tel or tel[-8:] in re.sub(r"\D", "", h), f"{s}: real phone number missing"
print("ok:", len(list(ROOT.glob("*/index.html"))), "pages checked,", len(mine) if PRIV.is_dir() else 0, "business demos x 3 variants")
