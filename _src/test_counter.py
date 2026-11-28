"""python _src/test_counter.py : the opens counter for the business demos (needs node for the behaviour part).
- the script counts once, after 5 s, only when the page is visible, and never in a browser that was told to skip
- the page policy allows the counter host for pictures and nothing else new
- while privats/counter.json is missing, no page contains the counter"""
import json, os, pathlib, re, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "_src"))
from counter import MARK, host, inject, snippet
from security import harden

try:
    snippet("Bad Code!")
    raise SystemExit("a bad counter code must be refused")
except AssertionError:
    pass

page = '<!doctype html><html><head><meta charset="utf-8"></head><body><p>x</p></body></html>'
one = inject(page, "demo-code")
assert one.count(MARK) == 1 and inject(one, "demo-code") == one, "inject must add the counter exactly once"
hard = harden(one, private=True, img_hosts=(host("demo-code"),))
assert "img-src 'self' data: https://demo-code.goatcounter.com;" in hard and "script-src 'sha256-" in hard
assert "demo-code" not in harden(page, private=True), "no counter host without a counter"

js = re.search(r"<script>(.*?)</script>", snippet("demo-code"), re.S).group(1)
harness = """
function run(opts) {
  const timers = [], images = [], store = Object.assign({}, opts.store || {});
  global.localStorage = { getItem: k => store[k] || null, setItem: (k, v) => { store[k] = v; } };
  global.location = { search: opts.search || '', pathname: '/website-demos/bergs-serviss/' };
  global.document = { visibilityState: opts.vis || 'visible', referrer: 'https://mail.example/' };
  global.setTimeout = (f, ms) => timers.push([f, ms]);
  global.Image = function () { images.push(this); };
  eval(JS);
  timers.forEach(([f]) => f());
  return { timers: timers.map(t => t[1]), images: images.map(i => i.src), skip: store.skipme || null };
}
const out = {
  normal: run({}), skipped: run({ store: { skipme: '1' } }), skipUrl: run({ search: '?skip' }), hidden: run({ vis: 'hidden' }),
};
console.log(JSON.stringify(out));
"""
r = subprocess.run(["node", "-e", "const JS=" + json.dumps(js) + ";" + harness], capture_output=True, text=True, check=True)
o = json.loads(r.stdout)
assert o["normal"]["timers"] == [5000] and len(o["normal"]["images"]) == 1, o["normal"]
img = o["normal"]["images"][0]
assert img.startswith("https://demo-code.goatcounter.com/count?p=%2Fwebsite-demos%2Fbergs-serviss%2F&r=https%3A%2F%2Fmail.example%2F&rnd="), img
assert o["skipped"]["timers"] == [] and o["skipped"]["images"] == [], "a browser with skipme must not be counted"
assert o["skipUrl"]["skip"] == "1" and o["skipUrl"]["images"] == [], "?skip must switch counting off for this browser"
assert o["hidden"]["timers"] == [5000] and o["hidden"]["images"] == [], "a page that is not visible after 5 s must not be counted"

if not (ROOT / "privats" / "counter.json").exists():
    leaks = [f.parent.name for f in ROOT.glob("*/index.html") if "goatcounter" in f.read_text(encoding="utf-8")]
    assert not leaks, f"counter found in pages although privats/counter.json is missing: {leaks}"
print("ok: counts once after 5 s when visible, respects skip, policy allows only the counter host")
