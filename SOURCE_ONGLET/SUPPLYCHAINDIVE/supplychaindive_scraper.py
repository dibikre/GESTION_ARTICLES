#!/usr/bin/env python3
"""
Navigation interactive dans l'API de Supply Chain Dive :
https://www.supplychaindive.com/api/v1/newsletteritemnewspost/

Affiche pour chaque article : titre, date, url de l'image (+ url de l'article).
Seuls les articles dont l'URL ne renvoie pas 404 sont affichés
(les brouillons / articles programmés ne sont donc pas listés).

Note : l'API ne fournit pas d'image. L'URL de l'image est lue dans la balise
<meta property="og:image"> de la page de l'article, récupérée au passage lors
de la vérification du 404 (une seule requête par article).

Dépendances :
    pip install requests beautifulsoup4

Utilisation :
    python supplychaindive_scraper.py            # démarre à la page 1
    python supplychaindive_scraper.py --page 5   # démarre à la page 5

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
import math
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

API_URL = "https://www.supplychaindive.com/api/v1/newsletteritemnewspost/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
MAX_WORKERS = 8


# --------------------------------------------------------------------------- #
# Récupération & parsing
# --------------------------------------------------------------------------- #
def clean_image_url(url: str) -> str:
    """Retire les paramètres de redimensionnement éventuels (?w=...&h=...)."""
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc, p.path, "", ""))


def parse_date(raw: str) -> str:
    """'2026-10-09T11:48:00' -> '2026-10-09' (texte brut si échec)."""
    return raw.split("T")[0] if raw else ""


def extract_image(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    meta = soup.find("meta", property="og:image") or soup.find(
        "meta", attrs={"name": "twitter:image"}
    )
    if meta and meta.get("content"):
        return clean_image_url(meta["content"])
    return None


def check_article(session: requests.Session, item: dict) -> dict | None:
    """Retourne l'article formaté, ou None si son URL renvoie 404."""
    url = item.get("source_url")
    if not url:
        return None

    image_url = None
    try:
        resp = session.get(url, headers=HEADERS, timeout=20)
    except requests.RequestException:
        # Erreur réseau : on ne peut pas affirmer que c'est un 404 -> on garde.
        pass
    else:
        if resp.status_code in (404, 410):
            return None
        if resp.ok:
            image_url = extract_image(resp.text)

    return {
        "title": (item.get("title") or "").strip(),
        "date": parse_date(item.get("pub_date", "")),
        "image_url": image_url,
        "url": url,
    }


def fetch_page(session: requests.Session, page: int) -> tuple[list[dict], int, int | None, int]:
    """Retourne (articles_valides, page, derniere_page, nb_resultats_api)."""
    resp = session.get(API_URL, params={"page": page}, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    results = data.get("results", [])
    count = data.get("count")
    last = math.ceil(count / len(results)) if count and results else None

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        checked = list(pool.map(lambda it: check_article(session, it), results))

    articles = [a for a in checked if a]
    return articles, page, last, len(results)


# --------------------------------------------------------------------------- #
# Affichage & export
# --------------------------------------------------------------------------- #
def show(articles: list[dict], page: int, last: int | None, total_api: int) -> None:
    total = f"/{last}" if last else ""
    hidden = total_api - len(articles)
    print("\n" + "=" * 70)
    print(f" PAGE {page}{total}  -  {len(articles)} articles ({hidden} en 404 ignorés)")
    print("=" * 70)
    for i, a in enumerate(articles, 1):
        print(f"\n{i:>2}. {a['title']}")
        print(f"    Date  : {a['date']}")
        print(f"    Image : {a['image_url']}")
        print(f"    URL   : {a['url']}")


def export(articles: list[dict], page: int, fmt: str) -> None:
    name = f"supplychaindive_page_{page}.{fmt}"
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
    ap = argparse.ArgumentParser(description="Navigation interactive Supply Chain Dive")
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
                    articles, page, last, total_api = fetch_page(session, page)
                except requests.RequestException as exc:
                    print(f"[!] Impossible de charger la page {page} : {exc}")
                    articles = []
                else:
                    show(articles, page, last, total_api)
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
