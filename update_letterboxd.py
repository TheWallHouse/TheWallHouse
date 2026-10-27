"""Actualiza la sección "Films & Series" del README con las últimas películas
vistas en Letterboxd, con carátula, año y nota.

- Lee el RSS público de Letterboxd (solo entradas del diario, es decir,
  películas marcadas como vistas).
- Descarga las carátulas a la carpeta posters/ para que GitHub las muestre
  siempre (las URLs externas a veces no cargan en los README).
- Sustituye lo que hay entre <!-- LETTERBOXD:START --> y <!-- LETTERBOXD:END -->.
"""

import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

USERNAME = os.environ.get("LETTERBOXD_USER", "TheWallHouse")
MAX_FILMS = int(os.environ.get("LETTERBOXD_MAX", "8"))
POSTER_WIDTH = 110  # px en el README
FEED_URL = f"https://letterboxd.com/{USERNAME}/rss/"
README = Path("README.md")
POSTERS_DIR = Path("posters")
START, END = "<!-- LETTERBOXD:START -->", "<!-- LETTERBOXD:END -->"
NS = {"lb": "https://letterboxd.com"}
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; letterboxd-readme-updater)"}


def stars(rating: str) -> str:
    """'3.5' -> '★★★½'"""
    if not rating:
        return ""
    value = float(rating)
    full = int(value)
    return "★" * full + ("½" if value - full >= 0.5 else "")


def fetch_films():
    resp = requests.get(FEED_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    films = []
    for item in root.findall("./channel/item"):
        title = item.findtext("lb:filmTitle", namespaces=NS)
        if not title:  # listas, reseñas sin película, etc.
            continue
        desc = item.findtext("description") or ""
        match = re.search(r'<img src="([^"]+)"', desc)
        if not match:
            continue
        # Pedimos la versión pequeña de la carátula (230x345) en vez de 600x900
        poster = re.sub(r"-0-\d+-0-\d+-crop", "-0-230-0-345-crop", match.group(1))
        films.append(
            {
                "title": title,
                "year": item.findtext("lb:filmYear", namespaces=NS) or "",
                "rating": item.findtext("lb:memberRating", namespaces=NS) or "",
                "rewatch": (item.findtext("lb:rewatch", namespaces=NS) or "No") == "Yes",
                "link": item.findtext("link") or "",
                "poster": poster,
            }
        )
        if len(films) >= MAX_FILMS:
            break
    return films


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def download_posters(films):
    POSTERS_DIR.mkdir(exist_ok=True)
    wanted = set()
    for film in films:
        name = f"{slugify(film['title'])}-{film['year']}.jpg"
        path = POSTERS_DIR / name
        wanted.add(name)
        if not path.exists():
            r = requests.get(film["poster"], headers=HEADERS, timeout=30)
            r.raise_for_status()
            path.write_bytes(r.content)
        film["local"] = f"{POSTERS_DIR}/{name}"
    # Borra carátulas de películas que ya no salen
    for old in POSTERS_DIR.glob("*.jpg"):
        if old.name not in wanted:
            old.unlink()


def render(films) -> str:
    if not films:
        return "<p align=\"center\"><i>Todavía no hay películas en el diario de Letterboxd.</i></p>"
    cells = []
    for f in films:
        caption = f"<b>{f['title']}</b> ({f['year']})"
        extra = " ".join(x for x in (stars(f["rating"]), "🔁" if f["rewatch"] else "") if x)
        if extra:
            caption += f"<br>{extra}"
        cells.append(
            f'<td align="center" valign="top" width="{POSTER_WIDTH + 20}">'
            f'<a href="{f["link"]}"><img src="{f["local"]}" width="{POSTER_WIDTH}" '
            f'alt="{f["title"]} ({f["year"]})"></a><br><sub>{caption}</sub></td>'
        )
    profile = f"https://letterboxd.com/{USERNAME}/"
    return (
        '<p align="center"><b>Últimas películas vistas</b> · '
        f'<a href="{profile}">Letterboxd</a></p>\n'
        '<table align="center"><tr>\n' + "\n".join(cells) + "\n</tr></table>"
    )


def main():
    films = fetch_films()
    download_posters(films)
    block = render(films)

    content = README.read_text(encoding="utf-8")
    if START not in content or END not in content:
        sys.exit(f"No encuentro los marcadores {START} / {END} en README.md")
    before = content.split(START)[0]
    after = content.split(END)[1]
    README.write_text(f"{before}{START}\n{block}\n{END}{after}", encoding="utf-8")
    print(f"README actualizado con {len(films)} película(s)")


if __name__ == "__main__":
    main()
