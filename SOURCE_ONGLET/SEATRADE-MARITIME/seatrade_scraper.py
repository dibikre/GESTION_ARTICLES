#!/usr/bin/env python3
"""
Navigation interactive dans les dernières actualités de Seatrade Maritime :
https://www.seatrade-maritime.com/latest-news

Affiche pour chaque article : titre, date, url de l'image (+ url de l'article).

Source des données : https://www.seatrade-maritime.com/latest-news.data
Ce n'est pas du JSON classique mais le format "single fetch" de React Router (turbo-stream) :
un grand tableau plat où les objets / listes se référencent par leur position. Le script le
décode, puis lit  routes/$topic._index -> data -> template :
    - contents    : la liste des articles (35 par page)
        articleName, articleUrl (relatif), date ("Oct 9, 2026"), thumbnail.src, contentType
    - pagination  : {"totalCount": 842, "currentPage": 1}

PAGINATION
    Le numéro de page est envoyé dans le paramètre d'URL PAGE_PARAM (par défaut "page",
    option --page-param pour le changer). La réponse renvoie "currentPage" : si elle ne
    correspond pas à la page demandée, le script le signale (paramètre incorrect).
    Le nombre de pages est calculé avec totalCount.

Dépendances :
    pip install requests

Utilisation :
    python seatrade_scraper.py                       # démarre à la page 1
    python seatrade_scraper.py --page 5              # démarre à la page 5
    python seatrade_scraper.py --page-param p        # autre nom de paramètre de pagination

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
from datetime import datetime
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests

SITE = "https://www.seatrade-maritime.com"
DATA_URL = SITE + "/latest-news.data"
PAGE_PARAM = "page"  # nom du paramètre d'URL qui porte le numéro de page
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


# --------------------------------------------------------------------------- #
# Décodage du format React Router "turbo-stream"
# --------------------------------------------------------------------------- #
def decode_turbo(flat: list):
    """Reconstruit l'objet d'origine : les valeurs entières sont des positions dans le tableau
    (négatif : -5 = null, -7 = undefined...), les clés d'objet sont "_<position du nom>"."""
    cache: dict[int, object] = {}

    def resolve(i: int):
        if i < 0:
            return None
        if i in cache:
            return cache[i]
        v = flat[i]
        if isinstance(v, dict):
            out: dict = {}
            cache[i] = out
            for k, x in v.items():
                name = flat[int(k[1:])] if k.startswith("_") and k[1:].isdigit() else k
                out[name] = resolve(x) if isinstance(x, int) and not isinstance(x, bool) else x
            return out
        if isinstance(v, list):
            if len(v) == 2 and v[0] == "D" and isinstance(v[1], (int, float)):  # date en millisecondes
                cache[i] = datetime.utcfromtimestamp(v[1] / 1000).isoformat()
                return cache[i]
            out_l: list = []
            cache[i] = out_l
            out_l.extend(resolve(x) if isinstance(x, int) and not isinstance(x, bool) else x for x in v)
            return out_l
        cache[i] = v
        return v

    return resolve(0)


def find_template(decoded: dict) -> dict:
    """Le bloc de données de la liste : routes/$topic._index -> data -> template."""
    for key, route in decoded.items():
        if isinstance(route, dict) and isinstance(route.get("data"), dict) and "template" in route["data"]:
            return route["data"]["template"]
    raise ValueError("bloc 'template' introuvable dans la réponse")


# --------------------------------------------------------------------------- #
# Récupération & parsing
# --------------------------------------------------------------------------- #
def clean_image_url(url: str) -> str:
    """Retire les paramètres de redimensionnement (?width=..&height=..) de l'image."""
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc, p.path, "", ""))


def parse_date(raw: str) -> str:
    """'Oct 9, 2026' -> '2026-10-09' (texte brut si échec)."""
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(raw.strip(), fmt).date().isoformat()
        except ValueError:
            pass
    return raw.strip()


def parse_items(contents: list[dict]) -> list[dict]:
    articles, seen = [], set()
    for c in contents:
        title = (c.get("articleName") or c.get("mobileHeadline") or "").strip()
        path = c.get("articleUrl") or ""
        if not (title and path):
            continue
        url = urljoin(SITE + "/", path)
        if url in seen:
            continue
        seen.add(url)
        thumb = c.get("thumbnail") or {}
        image = thumb.get("src")
        kind = c.get("contentType") or ""
        articles.append(
            {
                "title": title if kind in ("", "Article") else f"[{kind}] {title}",
                "date": parse_date(c.get("date") or ""),
                "image_url": clean_image_url(image) if image else None,
                "url": url,
            }
        )
    return articles


def fetch_page(session: requests.Session, page: int, page_param: str) -> tuple[list[dict], int, int, int]:
    """Renvoie (articles, page renvoyée par le site, total d'articles, nombre d'entrées de la page)."""
    params = {page_param: page} if page > 1 else {}
    resp = session.get(DATA_URL, params=params, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    template = find_template(decode_turbo(resp.json()))
    contents = template.get("contents") or []
    pag = template.get("pagination") or {}
    return (
        parse_items(contents),
        int(pag.get("currentPage") or 1),
        int(pag.get("totalCount") or 0),
        len(contents),
    )


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
    name = f"seatrade_page_{page}.{fmt}"
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
    ap = argparse.ArgumentParser(description="Navigation interactive Seatrade Maritime")
    ap.add_argument("--page", type=int, default=1, help="Page de départ (défaut: 1)")
    ap.add_argument("--page-param", default=PAGE_PARAM, help=f"Paramètre d'URL de pagination (défaut: {PAGE_PARAM})")
    args = ap.parse_args()

    page = max(1, args.page)
    last: int | None = None
    page_size = 0
    articles: list[dict] = []
    need_fetch = True

    with requests.Session() as session:
        while True:
            if need_fetch:
                try:
                    new, got_page, total, size = fetch_page(session, page, args.page_param)
                except (requests.RequestException, ValueError, KeyError) as exc:
                    print(f"[!] Impossible de charger la page {page} : {exc}")
                    articles = []
                else:
                    page_size = max(page_size, size)
                    if total and page_size:
                        last = max(1, math.ceil(total / page_size))
                    if got_page != page:
                        print(
                            f"[!] Le site a renvoyé la page {got_page} au lieu de la page {page} : "
                            f"le paramètre de pagination '{args.page_param}' ne semble pas pris en compte "
                            f"(essayez --page-param avec le nom vu dans l'onglet Réseau du navigateur)."
                        )
                        page = got_page
                    elif not new:
                        print(f"[!] La page {page} ne contient aucun article.")
                        articles = []
                    else:
                        articles = new
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
