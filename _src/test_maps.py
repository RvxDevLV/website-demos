"""python _src/test_maps.py : map picture is 1000x500, and a failed download leaves no broken picture in the page."""
import io, os, pathlib, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import maps

PAGE = '<div class="map" data-geo="57.5,25.4"><a class="map-img" href="#"><img src="karte.webp"></a><small class="credit">Karte © OpenStreetMap</small></div>'
png = io.BytesIO(); Image.new("RGB", (256, 256), "#f2efe9").save(png, "PNG")

with tempfile.TemporaryDirectory() as d:
    d = pathlib.Path(d)
    ok = maps.finish_map(PAGE, d, d / "c", get=lambda u: png.getvalue())          # fake tile server
    assert ok == PAGE and Image.open(d / "karte.webp").size == (1000, 500)
    # a cached tile that is not an image is replaced, not fatal
    bad_tile = d / "c" / sorted(os.listdir(d / "c"))[0]
    bad_tile.write_bytes(b"junk")
    maps.finish_map(PAGE, d, d / "c", get=lambda u: png.getvalue())
    Image.open(bad_tile).load()  # replaced by a real image
    assert not [f for f in os.listdir(d / "c") if f.endswith(".part")]
    # download fails: no picture, no credit, address card stays
    d2 = d / "x"; d2.mkdir()
    bad = maps.finish_map(PAGE, d2, d2 / "c", get=lambda u: (_ for _ in ()).throw(OSError("offline")))
    assert "map-img" not in bad and "OpenStreetMap" not in bad and not (d2 / "karte.webp").exists()
print("ok")
