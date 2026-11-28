"""Content-Security-Policy and referrer policy for the pages. GitHub Pages cannot send HTTP headers, so both go in <meta> tags.

harden(page) lists the hash of every inline script, so only the scripts that are really in the page can run
(a script injected later is blocked). Edit an inline script and run the build or `python _src/security.py index.html`
again, otherwise the browser blocks the edited script. test_build.py checks that every hash matches.

Not possible in <meta>: frame-ancestors / X-Frame-Options (clickjacking), Permissions-Policy, HSTS. They need a host that sends headers.
"""
import base64, hashlib, pathlib, re, sys

INLINE = re.compile(r'<script(?![^>]*\bsrc=)(?![^>]*type="application/ld\+json")[^>]*>(.*?)</script>', re.S)
OLD = re.compile(r'<meta http-equiv="Content-Security-Policy"[^>]*>\n?|<meta name="referrer"[^>]*>\n?')


def script_hash(text):
    return "'sha256-" + base64.b64encode(hashlib.sha256(text.encode("utf-8")).digest()).decode() + "'"


def harden(page, private=False, img_hosts=()):
    """private: a business demo whose address should not travel to other sites in the Referer header.
    img_hosts: extra hosts a picture may load from (the opens counter is a one-pixel request)."""
    page = OLD.sub("", page)
    scripts = " ".join(script_hash(s) for s in INLINE.findall(page)) or "'none'"
    connect = "'self' https://api.web3forms.com" if "https://api.web3forms.com/submit" in page else "'none'"
    csp = (f"default-src 'none'; script-src {scripts}; style-src 'self' 'unsafe-inline'; img-src 'self' data:{''.join(' https://' + h for h in img_hosts)}; font-src 'self'; "
           f"connect-src {connect}; base-uri 'none'; form-action 'self'; object-src 'none'; upgrade-insecure-requests")
    meta = (f'<meta http-equiv="Content-Security-Policy" content="{csp}">\n'
            f'<meta name="referrer" content="{"no-referrer" if private else "strict-origin-when-cross-origin"}">\n')
    head = '<meta charset="utf-8">'
    assert head in page, "page has no <meta charset> to put the policy after"
    return page.replace(head, head + "\n" + meta.rstrip("\n"), 1)


if __name__ == "__main__":  # hand-written pages: python _src/security.py index.html privatums.html
    for f in sys.argv[1:]:
        p = pathlib.Path(f)
        p.write_text(harden(p.read_text(encoding="utf-8")), encoding="utf-8")
        print("hardened", f)
