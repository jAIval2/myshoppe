"""Download development reference media; merchant photography replaces these at launch."""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[1] / "web/public/media"
root.mkdir(parents=True, exist_ok=True)
photos = {
    "campaign-women": "1539109136881-3be0616acf4b",
    "campaign-home": "1631049307264-da0ec9d70304",
    "woman-1": "1539109136881-3be0616acf4b",
    "woman-2": "1483985988355-763728e1935b",
    "woman-3": "1524504388940-b1c1722653e1",
    "woman-4": "1509631179647-0177331693ae",
    "woman-5": "1550614000-4895a10e1bfd",
    "woman-6": "1490481651871-ab68de25d43d",
    "home-1": "1631049307264-da0ec9d70304",
    "home-2": "1611892440504-42a792e24d32",
    "home-3": "1616594039964-ae9021a400a0",
    "home-4": "1615874959474-d609969a20ed",
}


def download(item):
    name, photo = item
    url = f"https://images.unsplash.com/photo-{photo}?auto=format&fit=crop&w=1800&q=85"
    target = root / f"{name}.jpg"
    if not target.exists() or name in ("woman-3", "woman-4", "woman-5", "woman-6"):
        with urlopen(
            Request(url, headers={"User-Agent": "MyShoppe development preview"}),
            timeout=45,
        ) as r:
            target.write_bytes(r.read())
    return {
        "asset": target.name,
        "source": url,
        "usage": "Development editorial placeholder; not a photograph of sellable inventory",
    }


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(download, photos.items()))
    records.append(
        {
            "asset": "campaign.mp4",
            "source": "https://www.pexels.com/video/853800/",
            "usage": "Development clothing-rack film; replace with owned Women and Home campaign films",
        }
    )
    (root / "sources.json").write_text(json.dumps(records, indent=2))
    print(f"Downloaded {len(records)} development photographs")
