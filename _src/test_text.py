"""python _src/test_text.py : fails on Latvian mistakes the grammar app cannot catch, and on the owner's style decisions.
Each rule comes from privats/gramatika/noteikumi.md. Add a rule when a new kind of mistake is found."""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRIV = ROOT / "privats"
FILES = [ROOT / "index.html", ROOT / "privatums.html", ROOT / "README.md", ROOT / "epasts.json", ROOT / "_src" / "build.py", ROOT / "_src" / "autoserviss.html",
         *sorted(ROOT.glob("*/index.html"))]
for extra in ("zvans.html", "zvana-teksts.html"):  # the private call tools, only when this computer has them
    if (PRIV / extra).exists():
        FILES.append(PRIV / extra)

EN = chr(0x2013)
RULES = [  # (regex, what is wrong, what to write, prose_only)
    (r"\bpēc trīs (mēnešiem|dienām|nedēļām|gadiem|stundām|minūtēm)", "numeral case after 'pēc'", "pēc trim …", False),
    (r"\bjūs (tur )?nav\b", "pronoun after 'nav' must be genitive", "jūsu … nav", False),
    (r"\buz (telefona|planšetes)\b", "calque", "telefonā / planšetē", False),
    (r"\buz pieraksta\b", "calque", "pēc pieraksta", False),
    (r"\b(Apskatāt|apskatāt|Skatāt|skatāt)\b|[Aa]pskatīt (paraugu|lapu)", "rejected wording for the reader (skatāt/apskatāt)", "aplūkot / aplūkojiet", False),
    (r"\b(Pasakāt|Maksājat, kad)\b", "rejected wording", "Pasakiet / Maksājiet", False),
    (r"lai (meklētājs saprot|tā parādās|mājaslapa parādās|jūs varat|jūs parādāties|klienti jūs atrod|potenciālie klienti jūs var\b)","'lai' needs the -tu form", "saprastu / parādītos / varētu / atrastu", False),
    (r"\bnākamnedēļ\b", "not standard", "nākamajā nedēļā", False),
    (r"Google kartēs\b", "plural slip", "Google kartē", False),
    (r"\bnosūtat\b", "typo", "nosūtāt", False),
    (r"\d%", "space before the percent sign", "25 %", True),
    (r"\d€", "space before the euro sign", "100 €", True),
    (r"\bu\.c\.|\bt\.i\.|\bu\.tml\.", "abbreviations take spaces", "u. c.  t. i.  u. tml.", False),
    (r"(?<=[\w.])" + EN + r"(?=\w)", "ranges use a hyphen (owner decision)", "10-20 €, 9.00-18.00", False),
]  # "pa telefonu" is an accepted idiom (Standarta leaves it), so it is not a rule


def blank(m):  # same length, so line numbers stay right
    return re.sub(r"[^\n]", " ", m.group(0))


bad = []
for f in FILES:
    text = f.read_text(encoding="utf-8")
    if f.suffix in (".html", ".md"):  # only what a visitor reads: no CSS, no scripts, no tags (the README has HTML tables)
        text = re.sub(r"<(script|style)\b.*?</\1>", blank, text, flags=re.S)
        text = re.sub(r"<[^>]*>", blank, text)
    if f.name == "build.py":  # comments are noise
        text = "\n".join(ln for ln in text.splitlines() if not ln.lstrip().startswith("#"))
    for rx, why, fix, prose_only in RULES:
        if prose_only and f.suffix == ".py":  # CSS inside Python strings: 50%, 100% are not prose
            continue
        for m in re.finditer(rx, text):
            line = text.count("\n", 0, m.start()) + 1
            bad.append(f"{f.relative_to(ROOT).as_posix()}:{line}: '{m.group(0)}': {why} -> {fix}")
    if "privats" not in f.parts:  # public text addresses a reader of any gender: no masculine participle after "esat" ("esat piekritis", "esat apmierināts")
        for m in re.finditer(r"\b(?:ne)?esat (?:[a-zāčēģīķļņšūž]+ )?[a-zāčēģīķļņšūž]+(?:is|ts)\b", text):
            line = text.count("\n", 0, m.start()) + 1
            bad.append(f"{f.relative_to(ROOT).as_posix()}:{line}: '{m.group(0)}': masculine form addressed to any reader -> plural 'esat piekrituši' or reword ('kad apstiprināt …')")

# structured data for Google also needs the hyphen in opening hours
for f in sorted(ROOT.glob("*/index.html")):
    if re.search(r'"openingHours": \[[^\]]*' + EN, f.read_text(encoding="utf-8")):
        bad.append(f"{f.relative_to(ROOT).as_posix()}: en dash in openingHours (schema.org needs a hyphen)")

# e-mail templates are letters to one person: Jūs/Jūsu/Jums with a capital letter
mail = json.loads((ROOT / "epasts.json").read_text(encoding="utf-8"))


def walk(o, path):
    if isinstance(o, str):
        for m in re.finditer(r"\b(jūs|jūsu|jums|jūsējiem)\b", o):
            bad.append(f"epasts.json:{path}: lowercase '{m.group(0)}' in an e-mail template -> capital letter")
    elif isinstance(o, dict):
        for k, v in o.items():
            if k not in ("version", "date"):
                walk(v, path + "/" + k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, f"{path}/{i}")


walk(mail, "")

# the website keeps lowercase 'jūs' inside a sentence (capital only at a sentence start)
for f in [ROOT / "index.html", ROOT / "privatums.html"]:
    body = re.sub(r"<(script|style)\b.*?</\1>", "", f.read_text(encoding="utf-8"), flags=re.S)
    for m in re.finditer(r"(?<=[a-zāčēģīķļņšūž,] )(Jūs|Jūsu|Jums)\b", re.sub(r"<[^>]+>", "", body)):
        bad.append(f"{f.name}: capital '{m.group(0)}' in the middle of a sentence -> lowercase on the website")

# the rules must catch what they claim to (a rule that matches nothing is silently broken)
for sample in ("pēc trīs mēnešiem", "jūs tur nav vispār", "darbojas uz telefona", "Apskatāt paraugu", "lai meklētājs saprot", "25%", "100€", "10" + EN + "20"):
    assert any(re.search(rx, sample) for rx, _, _, _ in RULES), f"rule set does not catch: {sample}"
assert re.search(r"\b(?:ne)?esat (?:[a-zāčēģīķļņšūž]+ )?[a-zāčēģīķļņšūž]+(?:is|ts)\b", "tikai tad, kad esat piekritis jaunajai cenai"), "gender rule is broken"
assert not re.search(r"\b(?:ne)?esat (?:[a-zāčēģīķļņšūž]+ )?[a-zāčēģīķļņšūž]+(?:is|ts)\b", "kad esat piekrituši jaunajai cenai un esat gatavi"), "gender rule is too wide"

if bad:
    print("\n".join(bad[:40]))
    sys.exit(f"{len(bad)} text problem(s)")
print("ok:", len(FILES), "files,", len(RULES), "rules")
