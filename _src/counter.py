"""Opens counter for the business demo pages (GoatCounter, cookieless). Off until privats/counter.json exists.

privats/counter.json = {"code": "yourcode", "token": "api-token-with-read-access"}
    code  : the site code, i.e. https://yourcode.goatcounter.com
    token : only the local send list reads it (to show the counts), it never goes into a page

The page sends one request to goatcounter.com, as a picture, after the page has been visible for 5 seconds. That filters most
mail scanners and link previews (they do not run scripts, or leave at once). A browser that has opened any demo with ?skip
at the end of the address is never counted (use it once on every browser you test with).
"""
import re

CODE = re.compile(r"[a-z0-9-]{2,40}")
MARK = "<!--counter-->"


def snippet(code):
    assert CODE.fullmatch(code), f"bad counter code: {code!r}"
    return (MARK + "<script>(function () {\n"
            "  try { if (localStorage.getItem('skipme')) return; if (/[?&]skip\\b/.test(location.search)) { localStorage.setItem('skipme', '1'); return; } } catch (e) {}\n"
            "  setTimeout(function () {\n"
            "    if (document.visibilityState !== 'visible') return;\n"
            f"    new Image().src = 'https://{code}.goatcounter.com/count?p=' + encodeURIComponent(location.pathname) + '&r=' + encodeURIComponent(document.referrer) + '&rnd=' + Math.random();\n"
            "  }, 5000);\n"
            "})();</script>\n")


def inject(page, code):
    """Add the counter once, just before </body>."""
    if MARK in page:
        return page
    assert "</body>" in page, "page has no </body>"
    return page.replace("</body>", snippet(code) + "</body>", 1)


def host(code):
    return f"{code}.goatcounter.com"
