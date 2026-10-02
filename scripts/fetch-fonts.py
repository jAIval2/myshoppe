"""Vendor the two OFL typefaces; no font CDN requests during shopping."""

import re
from pathlib import Path
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[1] / "web/public/fonts"
root.mkdir(parents=True, exist_ok=True)
for name, query in [
    ("inter", "Inter:wght@400..900"),
    ("bodoni", "Bodoni+Moda:opsz,wght@6..96,400..500"),
]:
    req = Request(
        f"https://fonts.googleapis.com/css2?family={query}&display=swap",
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        },
    )
    css = urlopen(req, timeout=30).read().decode()
    faces = re.findall(r"@font-face\s*\{[^}]+\}", css)
    latin = [face for face in faces if "U+0000-00FF" in face]
    if latin:
        css = "\n".join(latin)
    urls = list(dict.fromkeys(re.findall(r"url\((https://[^)]+)\)", css)))
    for i, url in enumerate(urls):
        extension = url.rsplit(".", 1)[-1]
        filename = f"{name}-{i}.{extension}"
        (root / filename).write_bytes(urlopen(url, timeout=30).read())
        css = css.replace(url, f"/fonts/{filename}")
    (root / f"{name}.css").write_text(css)
    print(f"{name}: {len(urls)} font files")
for folder, name in [("inter", "inter"), ("bodonimoda", "bodoni")]:
    url = f"https://raw.githubusercontent.com/google/fonts/main/ofl/{folder}/OFL.txt"
    (root / f"{name}-OFL.txt").write_bytes(urlopen(url, timeout=30).read())
