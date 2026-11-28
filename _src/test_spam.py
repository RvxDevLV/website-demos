"""python _src/test_spam.py : the portfolio form's spam filter (the spamReason function in index.html, run with node)."""
import json, pathlib, re, subprocess

html = (pathlib.Path(__file__).resolve().parent.parent / "index.html").read_text(encoding="utf-8")
fn = re.search(r"// spam-filter:start\n(.*?)// spam-filter:end", html, re.S).group(1)
ok = dict(name="Anna", contact="anna@example.lv", message="Labdien, gribu mājaslapu savam salonam.", website="", botcheck=False)
cases = [  # (changes to the good message, minutes of typing in ms, expected reason)
    ({}, 9000, ""),
    ({"contact": "+371 26 123 456"}, 9000, ""),                          # a phone number is fine
    ({"website": "http://spam.example"}, 9000, "bot"),                   # honeypot filled
    ({"botcheck": True}, 9000, "bot"),
    ({}, 1500, "fast"),                                                  # sent after 1.5 s
    ({}, 0, "fast"),                                                     # never typed anything
    ({"message": "Skatieties http://a.example un www.b.example"}, 9000, "links"),
    ({"message": "Skatieties https://mans.example"}, 9000, ""),         # one link is allowed
    ({"message": "Sveiki"}, 9000, "length"),
    ({"message": "x " * 600}, 9000, "length"),
    ({"contact": "abc"}, 9000, "contact"),
    ({"message": "Labdien!!!!!!!!!!!! vajag lapu"}, 9000, "repeat"),
]
js = fn + f"\nconst ok={json.dumps(ok)};\nconsole.log(JSON.stringify({json.dumps(cases)}.map(([c,ms])=>spamReason(Object.assign({{}},ok,c),ms))));"
got = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)
for (c, ms, want), g in zip(cases, got):
    assert g == want, f"{c} after {ms} ms: expected {want!r}, got {g!r}"
print("ok:", len(cases), "cases")
