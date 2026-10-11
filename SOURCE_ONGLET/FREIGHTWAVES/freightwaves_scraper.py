#!/usr/bin/env python3
"""
Navigation interactive dans https://www.freightwaves.com/news/category/news
Affiche pour chaque article : titre, date, url de l'image (+ url de l'article).

Dépendances :
    pip install requests beautifulsoup4

Utilisation :
    python freightwaves_scraper.py            # démarre à la page 1
    python freightwaves_scraper.py --page 5   # démarre à la page 5

Commandes pendant la navigation :
    n  (ou Entrée) -> page suivante
    p              -> page précédente
    <nombre>       -> aller directement à cette page
    f              -> première page
    l              -> dernière page
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

BASE_URL = "https://www.freightwaves.com/news/category/news"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# --------------------------------------------------------------------------- #
# Récupération & parsing
# --------------------------------------------------------------------------- #
def page_url(page: int) -> str:
    return BASE_URL if page <= 1 else f"{BASE_URL}/page/{page}"


def clean_image_url(url: str) -> str:
    """Retire les paramètres de redimensionnement (?w=390&h=220&crop=1)."""
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc, p.path, "", ""))


def parse_date(raw: str) -> str:
    """'Friday, October 9, 2026' -> '2026-10-09' (texte brut si échec)."""
    try:
        return datetime.strptime(raw, "%A, %B %d, %Y").date().isoformat()
    except ValueError:
        return raw


def parse_articles(soup: BeautifulSoup) -> list[dict]:
    articles = []
    for art in soup.select("main article"):
        h2 = art.select_one("h2.fw-block-post-title")
        if not h2:
            continue

        link = h2.find_parent("a")
        article_url = urljoin(BASE_URL, link["href"]) if link and link.get("href") else None

        date_raw = ""
        clock = art.select_one("i.tie-icon-clock")
        if clock and clock.parent:
            date_raw = clock.parent.get_text(strip=True)

        img = art.select_one("img.fw-block-post-thumbnail")
        image_url = clean_image_url(img["src"]) if img and img.get("src") else None

        articles.append(
            {
                "title": h2.get_text(strip=True),
                "date": parse_date(date_raw),
                "image_url": image_url,
                "url": article_url,
            }
        )
    return articles


def parse_pagination(soup: BeautifulSoup, fallback_page: int) -> tuple[int, int | None]:
    """Retourne (page_courante, derniere_page) depuis <ul class="fw-pagination">."""
    ul = soup.select_one("ul.fw-pagination")
    if not ul:
        return fallback_page, None

    current = fallback_page
    cur = ul.select_one("li.fw-pagination-current-item")
    if cur and cur.get_text(strip=True).isdigit():
        current = int(cur.get_text(strip=True))

    last = None
    last_a = ul.find("a", title="Last")
    if last_a and last_a.get("href"):
        m = re.search(r"/page/(\d+)", last_a["href"])
        if m:
            last = int(m.group(1))
    else:
        nums = [int(a.get_text(strip=True)) for a in ul.find_all("a")
                if a.get_text(strip=True).isdigit()]
        if nums:
            last = max(nums + [current])

    return current, last


def fetch_page(session: requests.Session, page: int) -> tuple[list[dict], int, int | None]:
    resp = session.get(page_url(page), headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    articles = parse_articles(soup)
    current, last = parse_pagination(soup, page)
    return articles, current, last


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
    name = f"freightwaves_page_{page}.{fmt}"
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
def main() -> None:
    ap = argparse.ArgumentParser(description="Navigation interactive FreightWaves News")
    ap.add_argument("--page", type=int, default=1, help="Page de départ (défaut: 1)")
    args = ap.parse_args()

    page = max(1, args.page)
    last: int | None = None
    articles: list[dict] = []
    need_fetch = True

    with requests.Session() as session:
        while True:
            if need_fetch:
                try:
                    articles, page, last = fetch_page(session, page)
                except requests.RequestException as exc:
                    print(f"[!] Impossible de charger la page {page} : {exc}")
                    articles = []
                else:
                    show(articles, page, last)
                need_fetch = False

            prompt = f"\n[n] suivant  [p] précédent  [numéro] aller à  [f] première  [l] dernière  [j/c] export  [q] quitter\n> "
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
                if last:
                    page, need_fetch = last, True
                else:
                    print("[!] Dernière page inconnue.")
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
