#!/usr/bin/env python3
"""
Navigation interactive dans les dernières actualités de STAT Times :
https://www.stattimes.com/latest-news   (page N : https://www.stattimes.com/latest-news/N)

Affiche pour chaque article : titre, date, url de l'image (+ url de l'article).

La liste est du HTML : chaque article est un bloc <article> du conteneur "listing-wrapper" avec
    - le titre + le lien   (h3.entry-title > a)
    - la date              (attribut data-datestring="2026-10-10 06:00:46" du <span class="s-post-date">)
    - l'image              (<img> de la colonne de droite : src / data-src)

PAGINATION
    Le bas de la liste contient un lien "Next Page" (https://www.stattimes.com/latest-news/2).
    Le site n'indique pas le nombre total de pages : la dernière page est celle qui n'a plus
    de lien "Next Page" (commande 'l' : le script avance jusqu'à elle).

Dépendances :
    pip install requests beautifulsoup4

Utilisation :
    python stattimes_scraper.py                 # démarre à la page 1
    python stattimes_scraper.py --page 5        # démarre à la page 5

Commandes pendant la navigation :
    n  (ou Entrée) -> page suivante
    p              -> page précédente
    <nombre>       -> aller directement à cette page
    f              -> première page
    l              -> dernière page (le script avance jusqu'à la dernière page existante)
    j / c          -> exporter la page courante en JSON / CSV
    q              -> quitter
"""

import argparse
import csv
import json
import re
from datetime import datetime
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

SITE = "https://www.stattimes.com"
LIST_URL = SITE + "/latest-news"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
MAX_SKIP_PAGES = 500  # garde-fou pour la commande 'l'


# --------------------------------------------------------------------------- #
# Récupération & parsing
# --------------------------------------------------------------------------- #
def clean_image_url(url: str) -> str:
    """Retire les paramètres d'URL éventuels de l'image."""
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc, p.path, "", ""))


def parse_date(tag) -> str:
    """data-datestring '2026-10-10 06:00:46' -> '2026-10-10' (sinon texte affiché '10 Oct 2026 7:00 AM')."""
    if tag is None:
        return ""
    raw = (tag.get("data-datestring") or "").strip()
    m = re.match(r"(\d{4}-\d{2}-\d{2})", raw)
    if m:
        return m.group(1)
    text = tag.get_text(" ", strip=True)
    for fmt in ("%d %b %Y %I:%M %p", "%d %B %Y %I:%M %p", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    return text


def parse_items(html: str) -> tuple[list[dict], bool]:
    """Renvoie (articles, il_y_a_une_page_suivante)."""
    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one(".listing-wrapper") or soup
    articles, seen = [], set()
    for art in root.find_all("article"):
        link = art.select_one("h3.entry-title a[href], .entry-title a[href], h3 a[href]")
        if not link:
            continue
        title = link.get_text(" ", strip=True)
        url = urljoin(SITE + "/", link["href"])
        if not title or url in seen:
            continue
        seen.add(url)

        img = art.select_one("img")
        image_url = None
        if img:
            for attr in ("data-src", "src", "data-lazy-src"):
                value = img.get(attr)
                if value and not value.startswith("data:") and "placeholder" not in value:
                    image_url = clean_image_url(urljoin(SITE + "/", value))
                    break

        articles.append(
            {
                "title": title,
                "date": parse_date(art.select_one(".s-post-date, [data-datestring]")),
                "image_url": image_url,
                "url": url,
            }
        )

    has_next = any(
        "next" in (a.get("class") or []) or "next page" in a.get_text(" ", strip=True).lower()
        for a in root.select(".pagination a")
    )
    return articles, has_next


def page_url(page: int) -> str:
    return LIST_URL if page <= 1 else f"{LIST_URL}/{page}"


def fetch_page(session: requests.Session, page: int) -> tuple[list[dict], bool]:
    resp = session.get(page_url(page), headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return parse_items(resp.text)


# --------------------------------------------------------------------------- #
# Affichage & export
# --------------------------------------------------------------------------- #
def show(articles: list[dict], page: int, last: int | None) -> None:
    total = f"/{last}" if last else ""
    print("\n" + "=" * 70)
    print(f" PAGE {page}{total}  -  {len(articles)} articles")
    print("=" * 70)
    for i, a in enumerate(articles, 1):
        print(f"\n{i:>2}. {a['title']}")
        print(f"    Date  : {a['date']}")
        print(f"    Image : {a['image_url']}")
        print(f"    URL   : {a['url']}")


def export(articles: list[dict], page: int, fmt: str) -> None:
    name = f"stattimes_page_{page}.{fmt}"
    if fmt == "json":
        with open(name, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
    else:
        with open(name, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["title", "date", "image_url", "url"])
            w.writeheader()
            w.writerows(articles)
    print(f"[✓] Exporté dans {name}")


# --------------------------------------------------------------------------- #
# Boucle interactive
# --------------------------------------------------------------------------- #
def find_last_page(session: requests.Session, start: int) -> int:
    """Avance de page en page (sans rien afficher) jusqu'à la page sans lien 'Next Page'."""
    page = start
    for _ in range(MAX_SKIP_PAGES):
        _, has_next = fetch_page(session, page)
        if not has_next:
            return page
        page += 1
        if page % 10 == 0:
            print(f"    ... page {page}")
    return page


def main() -> None:
    ap = argparse.ArgumentParser(description="Navigation interactive STAT Times")
    ap.add_argument("--page", type=int, default=1, help="Page de départ (défaut: 1)")
    args = ap.parse_args()

    page = max(1, args.page)
    last: int | None = None
    articles: list[dict] = []
    has_next = True
    need_fetch = True

    with requests.Session() as session:
        while True:
            if need_fetch:
                try:
                    new, has_next = fetch_page(session, page)
                except requests.RequestException as exc:
                    print(f"[!] Impossible de charger la page {page} : {exc}")
                    articles = []
                else:
                    if not new:
                        print(f"[!] La page {page} ne contient aucun article (fin de la liste ?).")
                        last = page - 1 if page > 1 else None
                        page = max(1, page - 1)
                        articles = []
                    else:
                        articles = new
                        if not has_next:
                            last = page
                        show(articles, page, last)
                need_fetch = False

            prompt = "\n[n] suivant  [p] précédent  [numéro] aller à  [f] première  [l] dernière  [j/c] export  [q] quitter\n> "
            cmd = input(prompt).strip().lower()

            if cmd in ("q", "quit", "exit"):
                print("Au revoir !")
                break
            elif cmd in ("", "n", "next"):
                if last and page >= last:
                    print("[!] Vous êtes déjà sur la dernière page.")
                    continue
                page += 1
                need_fetch = True
            elif cmd in ("p", "prev"):
                if page <= 1:
                    print("[!] Vous êtes déjà sur la première page.")
                    continue
                page -= 1
                need_fetch = True
            elif cmd == "f":
                page, need_fetch = 1, True
            elif cmd == "l":
                if not last:
                    print("[…] Recherche de la dernière page...")
                    try:
                        last = find_last_page(session, page)
                    except requests.RequestException as exc:
                        print(f"[!] Impossible de déterminer la dernière page : {exc}")
                        continue
                page, need_fetch = last, True
            elif cmd.isdigit():
                n = int(cmd)
                if n < 1 or (last and n > last):
                    print(f"[!] Numéro invalide (1 à {last or '?'}).")
                    continue
                page, need_fetch = n, True
            elif cmd in ("j", "c"):
                if articles:
                    export(articles, page, "json" if cmd == "j" else "csv")
                else:
                    print("[!] Rien à exporter.")
            else:
                print("[!] Commande inconnue.")


if __name__ == "__main__":
    main()
