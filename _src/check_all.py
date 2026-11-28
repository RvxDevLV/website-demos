"""python _src/check_all.py : runs every test of the project, prints one line per test and exits non-zero if any fails.
Run it before every commit. Takes about 2 minutes (test_build builds every demo three times)."""
import pathlib, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
TESTS = [("_src/test_text.py", "Latvian text rules"), ("_src/test_spam.py", "portfolio form spam filter"), ("_src/test_counter.py", "opens counter for the demos"), ("_src/test_maps.py", "map picture"),
         ("privats/test_income.py", "income and tax maths"), ("privats/test_serve.py", "send-list server security"),
         ("privats/test_remove.py", "remove-demo safety"), ("_src/test_build.py", "all pages: robots, policy, 3 variants")]
failed = []
for path, what in TESTS:
    p = ROOT / path
    if not p.exists():
        print(f"skip  {path} (private folder not on this computer)")
        continue
    t0 = time.time()
    r = subprocess.run([sys.executable, "-X", "utf8", str(p)], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    ok = r.returncode == 0
    tail = (r.stdout.strip().splitlines() or [""])[-1] if ok else (r.stdout + r.stderr).strip()[-600:]
    print(f"{'ok   ' if ok else 'FAIL '} {path:<26} {what:<40} {time.time() - t0:5.1f}s  {tail if ok else ''}")
    if not ok:
        print(tail)
        failed.append(path)
for d in list(ROOT.rglob("__pycache__")):
    if "privats" not in d.parts or d.parent.name in ("privats", "_src"):
        subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", str(d)], capture_output=True)
sys.exit(f"{len(failed)} test(s) failed: {', '.join(failed)}" if failed else 0)
