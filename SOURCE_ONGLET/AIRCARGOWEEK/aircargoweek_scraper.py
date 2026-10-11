#!/usr/bin/env python3
"""
Navigation interactive dans les actualités d'Air Cargo Week :
https://aircargoweek.com/news/?nocache=1

Affiche pour chaque article : titre, date, url de l'image (+ url de l'article).

Format de la réponse (JSON) : {"success": true, "data": {"html": "<div class='jet-listing-grid__item'>...", ...}}
Chaque article est un bloc "jet-listing-grid__item" contenant :
    - l'URL de l'article   (data-url du bloc / lien "jet-engine-listing-overlay-link")
    - l'image              (<img> de la vignette, redimensionnée en -500x333 : le suffixe est retiré)
    - la date              (<time>)
    - le titre             (.elementor-heading-title)

PAGINATION
    La réponse ne contient aucune information de pagination. Le numéro de page est envoyé
    dans le paramètre d'URL PAGE_PARAM (par défaut "jet_paged", option --page-param pour le changer).
    Si la page demandée renvoie les mêmes articles que la précédente ou aucun article,
    le script le signale (paramètre de pagination incorrect ou fin de la liste).

Dépendances :
    pip install requests beautifulsoup4

Utilisation :
    python aircargoweek_scraper.py                       # démarre à la page 1
    python aircargoweek_scraper.py --page 5              # démarre à la page 5
    python aircargoweek_scraper.py --page-param paged    # autre nom de paramètre de pagination

Commandes pendant la navigation :
    n  (ou Entrée) -> page suivante
    p              -> page précédente
    <nombre>       -> aller directement à cette page
    f              -> première page
    l              -> dernière page (connue seulement si elle a déjà été atteinte)
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

BASE_URL = "https://aircargoweek.com/news/"
PAGE_PARAM = "jet_paged"  # nom du paramètre d'URL qui porte le numéro de page
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
}


# --------------------------------------------------------------------------- #
# Récupération & parsing
# --------------------------------------------------------------------------- #
def clean_image_url(url: str) -> str:
    """Retire les paramètres d'URL et le suffixe de redimensionnement WordPress (-500x333)
    pour obtenir l'image d'origine : .../photo-500x333.jpg -> .../photo.jpg"""
    p = urlsplit(url)
    path = re.sub(r"-\d+x\d+(?=\.\w+$)", "", p.path)
    return urlunsplit((p.scheme, p.netloc, path, "", ""))


def parse_date(raw: str) -> str:
    """'October 2, 2026' -> '2026-10-02' (texte brut si échec)."""
    try:
        return datetime.strptime(raw.strip(), "%B %d, %Y").date().isoformat()
    except ValueError:
        return raw.strip()


def parse_items(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    articles, seen = [], set()
    for item in soup.select("div.jet-listing-grid__item"):
        post_id = item.get("data-post-id")

        url = None
        wrap = item.select_one("[data-url]")
        if wrap and wrap.get("data-url"):
            url = urljoin(BASE_URL, wrap["data-url"])
        else:
            link = item.select_one("a.jet-engine-listing-overlay-link[href]") or item.select_one("a[href]")
            if link:
                url = urljoin(BASE_URL, link["href"])

        title_tag = item.select_one(".elementor-heading-title")
        title = title_tag.get_text(" ", strip=True) if title_tag else ""
        if not (title and url):
            continue
        key = post_id or url
        if key in seen:
            continue
        seen.add(key)

        time_tag = item.select_one("time")
        date_raw = time_tag.get_text(strip=True) if time_tag else ""

        img = item.select_one("img")
        image_url = None
        if img:
            for attr in ("src", "data-src", "data-lazy-src"):
                value = img.get(attr)
                if value and not value.startswith("data:"):
                    image_url = clean_image_url(urljoin(BASE_URL, value))
                    break

        articles.append(
            {
                "title": title,
                "date": parse_date(date_raw),
                "image_url": image_url,
                "url": url,
            }
        )
    return articles


def extract_html(resp: requests.Response) -> str:
    """HTML de la liste : champ data.html du JSON (sinon la réponse elle-même si c'est du HTML)."""
    text = resp.text
    if text.lstrip().startswith("{"):
        data = resp.json()
        if not data.get("success", True):
            raise ValueError("réponse JSON avec success=false")
        return (data.get("data") or {}).get("html", "")
    return text


def fetch_page(session: requests.Session, page: int, page_param: str) -> list[dict]:
    params = {"nocache": 1}
    if page > 1:
        params[page_param] = page
    resp = session.get(BASE_URL, params=params, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return parse_items(extract_html(resp))


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
    name = f"aircargoweek_page_{page}.{fmt}"
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
    ap = argparse.ArgumentParser(description="Navigation interactive Air Cargo Week")
    ap.add_argument("--page", type=int, default=1, help="Page de départ (défaut: 1)")
    ap.add_argument("--page-param", default=PAGE_PARAM, help=f"Paramètre d'URL de pagination (défaut: {PAGE_PARAM})")
    args = ap.parse_args()

    page = max(1, args.page)
    last: int | None = None
    articles: list[dict] = []
    previous_urls: set[str] = set()
    need_fetch = True

    with requests.Session() as session:
        while True:
            if need_fetch:
                try:
                    new = fetch_page(session, page, args.page_param)
                except (requests.RequestException, ValueError) as exc:
                    print(f"[!] Impossible de charger la page {page} : {exc}")
                    articles = []
                else:
                    urls = {a["url"] for a in new}
                    if not new:
                        print(f"[!] La page {page} ne contient aucun article (fin de la liste ?).")
                        last = page - 1 if page > 1 else None
                        page = max(1, page - 1)
                    elif page > 1 and urls == previous_urls:
                        print(
                            f"[!] La page {page} renvoie les mêmes articles que la précédente : "
                            f"le paramètre de pagination '{args.page_param}' ne semble pas pris en compte "
                            f"(essayez --page-param avec le nom vu dans l'onglet Réseau du navigateur)."
                        )
                    else:
                        articles, previous_urls = new, urls
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
