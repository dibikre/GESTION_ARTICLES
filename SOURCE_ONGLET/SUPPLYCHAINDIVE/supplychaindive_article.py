#!/usr/bin/env python3
"""
Saisir le lien d'un article Supply Chain Dive -> affiche :
    - le titre
    - le sous-titre (en dessous)
    - le contenu de l'article, avec [IMAGE_N] à l'emplacement des images du milieu
      et [EMBED_N] à l'emplacement des contenus intégrés (iframe) : tableaux / graphiques
      Datawrapper, vidéos YouTube, etc.
    - à la fin, l'image principale, la liste des IMAGE_N et la liste des EMBED_N
      (avec légende / titre éventuel)

La date et l'auteur sont ignorés. Sont aussi retirés :
    - les mentions du type "(UPDATED 1:15 p.m. ET)"
    - les pubs, l'inscription à la newsletter, le lecteur audio, les carrousels
      "Read More in ..." et tout ce qui suit le corps de l'article
      ("Recommended Reading", "Filed Under", ...)

TABLEAUX / GRAPHIQUES
    Les tableaux de Supply Chain Dive sont des iframes Datawrapper. Ils sont repérés
    par [EMBED_N] dans le texte ; la fin de l'article donne l'URL de l'iframe
    et son titre, par ex. :
        EMBED_1 DANS LE MILIEU DE L'ARTICLE : https://datawrapper.dwcdn.net/q2aEm/5/|Top supply chain conferences in 2027
    Le tableau est détecté même si l'iframe est absente du HTML reçu (id du graphique
    retrouvé dans l'id / le script embed.js). Son contenu (CSV Datawrapper) est inséré
    juste après [EMBED_N] : lignes "a | b | c" en texte brut, vrai tableau HTML
    pour la copie avec mise en forme. Pour désactiver : INLINE_TABLES = False.

PRESSE-PAPIER
    'c' : copie AVEC la mise en forme de la page (titres, gras, italique, liens,
          paragraphes, listes) -> à coller dans Word, Gmail, Google Docs, etc.
    't' : copie en texte brut (comme affiché dans le terminal).

Dépendances :
    pip install requests beautifulsoup4
    pip install pyperclip        (optionnel : uniquement pour la copie en texte brut)

Utilisation :
    python supplychaindive_article.py                         # saisie interactive
    python supplychaindive_article.py <lien>                  # un seul article
    python supplychaindive_article.py <lien> --copy           # + copie avec mise en forme
    python supplychaindive_article.py <lien> --copy-text      # + copie en texte brut
"""

import argparse
import csv
import html as htmllib
import io
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup, Comment, NavigableString, Tag

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

SEPARATOR = "=" * 53

# Le contenu est coupé dès qu'un paragraphe / titre commence par l'un de ces textes
# (le bloc concerné et tout ce qui suit sont retirés)
END_MARKERS = (
    "more articles by",
    "click here for more",
    "related stories",
    "related articles",
    "recommended reading",
)

# Paragraphes ignorés (mais le contenu continue), ex : "(UPDATED 1:15 p.m. ET)"
IGNORED_PATTERNS = [
    re.compile(r"^\(\s*(update[d]?|correct(?:ed|ion)|editor.?s note)\b.*\)$", re.I),
]

SKIP_TAGS = {"script", "style", "iframe", "noscript", "link", "button", "form", "svg"}
# Blocs de la page à ignorer : pubs, newsletter, audio, carrousels, partage...
SKIP_CLASSES = {
    "text-to-speech",
    "hybrid-ad-wrapper",
    "inline-signup",
    "subscriber-demographics",
    "storylines-carousel-wrapper",
    "storylines-carousel",
    "signup",
    "article-box",
    "reading-list",
    "social-share",
    "share-buttons",
    "editors-pick-footer-mobile",
}
SKIP_CLASS_PREFIXES = ("hybrid-ad",)
SKIP_IDS = {"desktop-inline-signup", "mobile-inline-signup", "desktop-carousel", "mobile-carousel"}
TEXT_BLOCKS = {"h2", "h3", "h4", "h5", "h6"}
# Iframes conservées (vidéos, tableaux, graphiques). Les iframes publicitaires n'ont pas de src : elles sont ignorées.
EMBED_HOSTS = (
    "youtube.com",
    "youtube-nocookie.com",
    "youtu.be",
    "datawrapper.dwcdn.net",
    "datawrapper.de",
    "flo.uri.sh",
    "flourish.studio",
    "infogram.com",
    "public.tableau.com",
)
INLINE_KEPT = {"strong", "b", "em", "i", "u", "s", "strike", "sup", "sub"}  # mise en forme conservée

# Tableaux Datawrapper : True = le contenu du tableau (CSV de Datawrapper) est inséré dans le texte
# juste après [EMBED_N]. Mettre False pour ne garder que le repère [EMBED_N] + l'URL.
INLINE_TABLES = True
# Repère un identifiant Datawrapper (et sa version) dans une URL / un id / un script
DATAWRAPPER_RE = re.compile(r"datawrapper(?:\.dwcdn\.net|\.de)/(\w{4,6})(?:/(\d+))?|datawrapper-chart-(\w{4,6})")


@dataclass
class Article:
    text: str  # version texte brut (affichée dans le terminal)
    html: str  # version HTML (mise en forme de la page) pour le presse-papier


# --------------------------------------------------------------------------- #
# Utilitaires
# --------------------------------------------------------------------------- #
def clean_image_url(url: str) -> str:
    """Retire les paramètres de redimensionnement éventuels (?w=1200, ?w=970&h=546&crop=1)."""
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc, p.path, "", ""))


def clean_text(tag: Tag) -> str:
    parts = []
    for node in tag.descendants:  # lecture seule : l'arbre HTML n'est pas modifié
        if isinstance(node, Comment):
            continue
        if isinstance(node, NavigableString):
            if node.parent is None or node.parent.name not in SKIP_TAGS:
                parts.append(str(node))
        elif node.name == "br":
            parts.append("\n")
    text = "".join(parts).replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    return text.strip()


def _inline(node: Tag, base_url: str) -> str:
    parts = []
    for child in node.children:
        if isinstance(child, Comment):
            continue
        if isinstance(child, NavigableString):
            parts.append(htmllib.escape(str(child).replace("\xa0", " ")))
            continue
        if not isinstance(child, Tag) or is_skipped(child):
            continue
        if child.name == "br":
            parts.append("<br>")
            continue
        inner = _inline(child, base_url)
        if child.name == "a" and child.get("href") and inner.strip():
            href = htmllib.escape(urljoin(base_url, child["href"]), quote=True)
            parts.append(f'<a href="{href}">{inner}</a>')
        elif child.name in INLINE_KEPT and inner.strip():
            parts.append(f"<{child.name}>{inner}</{child.name}>")
        else:
            parts.append(inner)  # span, etc. : on garde le contenu, sans la balise
    return "".join(parts)


def inline_html(node: Tag, base_url: str) -> str:
    """Contenu HTML d'une balise, avec gras / italique / liens / retours à la ligne conservés."""
    out = re.sub(r"[ \t\r\n]+", " ", _inline(node, base_url))
    return re.sub(r"^(?:\s|<br>)+|(?:\s|<br>)+$", "", out)


def image_url(img: Tag, base_url: str) -> str | None:
    for attr in ("src", "data-src", "data-lazy-src"):
        value = img.get(attr)
        if value and not value.startswith("data:"):
            return clean_image_url(urljoin(base_url, value))
    return None


def embed_url(iframe: Tag, base_url: str) -> str | None:
    """URL de l'iframe si c'est un contenu intégré connu (Datawrapper, YouTube...), sinon None.
    Gère src / data-src (lazy-load)."""
    for attr in ("src", "data-src", "data-lazy-src"):
        value = iframe.get(attr)
        if not value or value.startswith(("data:", "about:")):
            continue
        url = urljoin(base_url, value.strip())  # gère aussi les liens "//datawrapper.dwcdn.net/..."
        host = (urlsplit(url).hostname or "").lower()
        if any(host == h or host.endswith("." + h) for h in EMBED_HOSTS):
            return url

    # Secours Datawrapper : l'id de l'iframe est "datawrapper-chart-<ID>"
    m = re.match(r"datawrapper-chart-(\w+)$", iframe.get("id") or "")
    if m:
        return f"https://datawrapper.dwcdn.net/{m.group(1)}/"
    return None


def is_skipped(tag: Tag) -> bool:
    if tag.name in SKIP_TAGS:
        return True
    if tag.get("id") in SKIP_IDS:
        return True
    classes = tag.get("class") or []
    return any(c in SKIP_CLASSES or c.startswith(SKIP_CLASS_PREFIXES) for c in classes)


def figure_caption(fig: Tag) -> str:
    """Légende d'une figure (sans la ligne de crédit photo)."""
    cap = fig.select_one(".caption_text")
    if cap:
        return clean_text(cap)
    caption_tag = fig.find("figcaption")
    return clean_text(caption_tag) if caption_tag else ""


def datawrapper_url(text: str) -> str | None:
    """URL Datawrapper reconstruite depuis n'importe quel texte contenant l'id du graphique
    (src d'iframe, id 'datawrapper-chart-XXXXX', script embed.js...)."""
    m = DATAWRAPPER_RE.search(text or "")
    if not m:
        return None
    chart_id, version, id_only = m.group(1), m.group(2), m.group(3)
    chart_id = chart_id or id_only
    return f"https://datawrapper.dwcdn.net/{chart_id}/{version + '/' if version else ''}"


def fetch_datawrapper_rows(url: str) -> list[list[str]] | None:
    """Télécharge les données (CSV) d'un tableau Datawrapper. None si impossible."""
    m = DATAWRAPPER_RE.search(url)
    if not m:
        return None
    chart_id, version = (m.group(1) or m.group(3)), m.group(2)
    candidates = []
    if version:
        candidates.append(f"https://datawrapper.dwcdn.net/{chart_id}/{version}/dataset.csv")
    candidates.append(f"https://datawrapper.dwcdn.net/{chart_id}/dataset.csv")
    for csv_url in candidates:
        try:
            resp = requests.get(csv_url, headers=HEADERS, timeout=20)
            if not resp.ok or not resp.text.strip():
                continue
            text = resp.content.decode("utf-8-sig", errors="replace")
            rows = [r for r in csv.reader(io.StringIO(text)) if any(c.strip() for c in r)]
            if rows:
                return rows
        except (requests.RequestException, csv.Error):
            continue
    return None


def table_blocks(rows: list[list[str]], base_url: str) -> tuple[str, str]:
    """(texte brut, html) d'un tableau : 1re ligne = en-tête. Les cellules peuvent contenir du HTML (liens...)."""

    def cell(raw: str) -> tuple[str, str]:
        node = BeautifulSoup(raw or "", "html.parser")
        return clean_text(node).replace("\n", " "), inline_html(node, base_url)

    parsed = [[cell(c) for c in row] for row in rows]
    plain = "\n".join(" | ".join(t for t, _ in row) for row in parsed)
    head, body = parsed[0], parsed[1:]
    html_out = "<table border=\"1\" cellpadding=\"4\" cellspacing=\"0\"><thead><tr>"
    html_out += "".join(f"<th>{h}</th>" for _, h in head) + "</tr></thead><tbody>"
    for row in body:
        html_out += "<tr>" + "".join(f"<td>{h}</td>" for _, h in row) + "</tr>"
    html_out += "</tbody></table>"
    return plain, html_out


# --------------------------------------------------------------------------- #
# Extraction du contenu
# --------------------------------------------------------------------------- #
class ContentExtractor:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.blocks: list[tuple[str, str]] = []  # (texte brut, html)
        self.images: list[tuple[str, str]] = []  # (url, légende)
        self.embeds: list[tuple[str, str]] = []  # (url iframe, légende / titre)
        self.stopped = False

    def add_image(self, img: Tag, caption: str = "") -> None:
        url = image_url(img, self.base_url)
        if not url or any(url == u for u, _ in self.images):
            return
        self.images.append((url, caption))
        placeholder = f"[IMAGE_{len(self.images)}]"
        self.blocks.append((placeholder, f"<p>{placeholder}</p>"))

    def add_embed(self, iframe: Tag, caption: str = "") -> None:
        url = embed_url(iframe, self.base_url)
        self.add_embed_url(url, caption or (iframe.get("title") or "").strip())

    def add_embed_url(self, url: str | None, caption: str = "") -> None:
        if not url or any(url == u for u, _ in self.embeds):
            return
        self.embeds.append((url, caption))
        placeholder = f"[EMBED_{len(self.embeds)}]"
        self.blocks.append((placeholder, f"<p>{placeholder}</p>"))
        # Tableau Datawrapper : on insère aussi son contenu juste après le repère
        if INLINE_TABLES and DATAWRAPPER_RE.search(url):
            rows = fetch_datawrapper_rows(url)
            if rows:
                plain, html_table = table_blocks(rows, self.base_url)
                self.blocks.append((plain, html_table))

    def add_media(self, elements: list[Tag], caption: str = "") -> None:
        """Images et iframes, dans l'ordre du document."""
        for el in elements:
            cap = caption if len(elements) == 1 else ""
            if el.name == "img":
                self.add_image(el, cap)
            else:
                self.add_embed(el, cap)

    def add_text(self, text: str, html_block: str) -> None:
        """Ajoute un bloc, sauf s'il est ignoré ; déclenche l'arrêt sur un marqueur de fin."""
        if text.lower().startswith(END_MARKERS):
            self.stopped = True
            return
        if not text or any(p.match(text) for p in IGNORED_PATTERNS):
            return
        self.blocks.append((text, html_block))

    def add_chart(self, node: Tag) -> None:
        """Bloc 'ed-chart' (tableau / graphique Datawrapper) : titre + iframe."""
        title_tag = node.select_one(".ed-chart__title")
        title = clean_text(title_tag) if title_tag else ""
        iframes = node.find_all("iframe")
        before = len(self.embeds)
        for iframe in iframes:
            self.add_embed(iframe, title)
        if len(self.embeds) == before:
            # Pas d'iframe exploitable dans le HTML reçu (elle est parfois créée par JavaScript) :
            # on retrouve l'id du graphique dans le bloc (id, src, script embed.js, data-*...)
            url = datawrapper_url(str(node))
            if url:
                self.add_embed_url(url, title)
            elif title:
                self.add_text(title, f"<p>{htmllib.escape(title)}</p>")

    def add_by_the_numbers(self, node: Tag) -> None:
        """Encadré 'By the numbers' : chiffre + description."""
        title_tag = node.select_one(".ed-bynumbers__title")
        title = clean_text(title_tag) if title_tag else "By the numbers"
        plain, items = [], []
        for item in node.select(".ed-bynumbers__item"):
            num_tag = item.select_one(".ed-bynumbers__number")
            txt_tag = item.select_one(".ed-bynumbers__text")
            num = clean_text(num_tag) if num_tag else ""
            txt = clean_text(txt_tag) if txt_tag else ""
            if not (num or txt):
                continue
            plain.append(f"- {num} : {txt}" if num and txt else f"- {num or txt}")
            items.append(
                f"<li><strong>{htmllib.escape(num)}</strong> : {inline_html(txt_tag, self.base_url)}</li>"
                if num and txt_tag
                else f"<li>{htmllib.escape(num or txt)}</li>"
            )
        if items:
            self.blocks.append(
                (title + "\n" + "\n".join(plain), f"<h4>{htmllib.escape(title)}</h4><ul>{''.join(items)}</ul>")
            )

    def walk(self, node: Tag) -> None:
        for child in node.children:
            if self.stopped:
                return
            if not isinstance(child, Tag):
                continue

            classes = child.get("class") or []
            if "ed-chart" in classes or "ed-chart__datawrapper" in classes:  # tableau / graphique Datawrapper
                self.add_chart(child)
                continue
            if child.name == "script" and "datawrapper" in (child.get("src") or ""):
                # <script src=".../ID/embed.js"> posé directement dans le texte
                self.add_embed_url(datawrapper_url(child["src"]))
                continue
            if "ed-bynumbers" in classes:
                self.add_by_the_numbers(child)
                continue
            if child.name == "iframe":  # seules les iframes connues (Datawrapper, YouTube...) sont gardées
                self.add_embed(child)
                continue
            if is_skipped(child):
                continue

            name = child.name
            if name == "p":
                self.add_media(child.find_all(["img", "iframe"]))
                self.add_text(clean_text(child), f"<p>{inline_html(child, self.base_url)}</p>")
            elif name in TEXT_BLOCKS:
                self.add_text(clean_text(child), f"<{name}>{inline_html(child, self.base_url)}</{name}>")
            elif name == "blockquote":
                paras = child.find_all("p")
                inner = "".join(f"<p>{inline_html(p, self.base_url)}</p>" for p in paras) or inline_html(child, self.base_url)
                self.add_text(clean_text(child), f"<blockquote>{inner}</blockquote>")
            elif name in ("ul", "ol"):
                lis = [li for li in child.find_all("li", recursive=False)]
                texts = [clean_text(li) for li in lis]
                if any(texts):
                    plain = "\n".join(f"- {t}" for t in texts if t)
                    items = "".join(f"<li>{inline_html(li, self.base_url)}</li>" for li, t in zip(lis, texts) if t)
                    self.blocks.append((plain, f"<{name}>{items}</{name}>"))
            elif name == "figure":
                self.add_media(child.find_all(["img", "iframe"]), figure_caption(child))
            elif name == "img":
                self.add_image(child)
            else:
                self.walk(child)  # div / section imbriquées


# --------------------------------------------------------------------------- #
# Construction de l'article
# --------------------------------------------------------------------------- #
def parse_article(html: str, base_url: str) -> Article:
    soup = BeautifulSoup(html, "html.parser")

    h1 = soup.select_one("article h1") or soup.find("h1")
    title = clean_text(h1) if h1 else "(titre introuvable)"
    title_html = inline_html(h1, base_url) if h1 else htmllib.escape(title)

    # Le sous-titre est le <p> juste sous le <h1>
    p_sub = h1.find_next_sibling("p") if h1 else None
    subtitle = clean_text(p_sub) if p_sub else ""
    subtitle_html = inline_html(p_sub, base_url) if p_sub else ""

    main_img = soup.select_one("figure.inside_story .article-hero-img img") or soup.select_one(
        ".article-hero-img img"
    )
    main_image_url = image_url(main_img, base_url) if main_img else None
    if not main_image_url:
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            main_image_url = clean_image_url(og["content"])

    content = soup.select_one("div.article-body") or soup.select_one(".article-body")
    extractor = ContentExtractor(base_url)
    if content:
        extractor.walk(content)

    # Bloc final des images
    image_lines = []
    if main_image_url:
        image_lines.append(f"IMAGE DE L'ARTICLE: {main_image_url}")
    for n, (url, caption) in enumerate(extractor.images, 1):
        line = f"IMAGE_{n} DANS LE MILIEU DE L'ARTICLE : {url}"
        if caption:
            line += f"|{caption}"
        image_lines.append(line)
    for n, (url, caption) in enumerate(extractor.embeds, 1):
        line = f"EMBED_{n} DANS LE MILIEU DE L'ARTICLE : {url}"
        if caption:
            line += f"|{caption}"
        image_lines.append(line)

    # --- version texte brut ---
    text_out = [title]
    if subtitle:
        text_out.append(subtitle)
    text_out.append("")
    text_out.append("\n\n".join(t for t, _ in extractor.blocks))
    if image_lines:
        text_out += ["", SEPARATOR, *image_lines, SEPARATOR]

    # --- version HTML (mise en forme de la page) ---
    html_out = [f"<h1>{title_html}</h1>"]
    if subtitle_html:
        html_out.append(f"<h2>{subtitle_html}</h2>")
    html_out += [h for _, h in extractor.blocks]
    if image_lines:
        lines = [SEPARATOR, *image_lines, SEPARATOR]
        html_out.append("<p>" + "<br>".join(htmllib.escape(l, quote=False) for l in lines) + "</p>")

    return Article(text="\n".join(text_out), html="\n".join(html_out))


def fetch_article(url: str) -> Article:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return parse_article(resp.text, url)


# --------------------------------------------------------------------------- #
# Presse-papier : TEXTE BRUT
# --------------------------------------------------------------------------- #
def copy_plain_text(text: str) -> bool:
    try:
        import pyperclip

        pyperclip.copy(text)
        return True
    except Exception:
        pass

    system = platform.system()
    try:
        if system == "Darwin" and shutil.which("pbcopy"):
            subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
            return True
        if system == "Windows" and shutil.which("clip"):
            data = b"\xff\xfe" + text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-16-le")
            subprocess.run(["clip"], input=data, check=True)
            return True
        if system == "Linux":
            for cmd in (["wl-copy"], ["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]):
                if shutil.which(cmd[0]):
                    subprocess.run(cmd, input=text.encode("utf-8"), check=True)
                    return True
    except (subprocess.SubprocessError, OSError):
        pass

    try:
        import tkinter

        root = tkinter.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
        return True
    except Exception:
        return False


# --------------------------------------------------------------------------- #
# Presse-papier : HTML (mise en forme de la page conservée)
# --------------------------------------------------------------------------- #
def wrap_html(fragment: str) -> str:
    return f'<html><head><meta charset="utf-8"></head><body>{fragment}</body></html>'


def build_cf_html(fragment: str) -> str:
    """Format 'HTML Format' du presse-papier Windows (CF_HTML) : en-tête avec offsets en octets."""
    header = "Version:0.9\r\nStartHTML:{:010d}\r\nEndHTML:{:010d}\r\nStartFragment:{:010d}\r\nEndFragment:{:010d}\r\n"
    pre = '<html><head><meta charset="utf-8"></head><body><!--StartFragment-->'
    post = "<!--EndFragment--></body></html>"
    start_html = len(header.format(0, 0, 0, 0).encode("ascii"))
    start_frag = start_html + len(pre.encode("utf-8"))
    end_frag = start_frag + len(fragment.encode("utf-8"))
    end_html = end_frag + len(post.encode("utf-8"))
    return header.format(start_html, end_html, start_frag, end_frag) + pre + fragment + post


def _copy_html_windows(fragment: str, plain: str) -> bool:
    import ctypes
    from ctypes import wintypes

    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = wintypes.LPVOID
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.RegisterClipboardFormatW.argtypes = [wintypes.LPCWSTR]
    user32.RegisterClipboardFormatW.restype = wintypes.UINT

    def put(fmt: int, data: bytes) -> bool:
        handle = kernel32.GlobalAlloc(0x0002, len(data))  # GMEM_MOVEABLE
        if not handle:
            return False
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            return False
        ctypes.memmove(ptr, data, len(data))
        kernel32.GlobalUnlock(handle)
        return bool(user32.SetClipboardData(fmt, handle))

    for _ in range(20):
        if user32.OpenClipboard(None):
            break
        time.sleep(0.05)
    else:
        return False
    try:
        user32.EmptyClipboard()
        ok_html = put(user32.RegisterClipboardFormatW("HTML Format"), build_cf_html(fragment).encode("utf-8") + b"\0")
        # Version texte brut en complément (pour les éditeurs sans mise en forme)
        put(13, (plain.replace("\r\n", "\n").replace("\n", "\r\n") + "\0").encode("utf-16-le"))  # CF_UNICODETEXT
        return ok_html
    finally:
        user32.CloseClipboard()


def copy_html_to_clipboard(fragment: str, plain: str) -> bool:
    system = platform.system()
    try:
        if system == "Windows":
            return _copy_html_windows(fragment, plain)
        if system == "Darwin" and shutil.which("osascript"):
            hexdata = wrap_html(fragment).encode("utf-8").hex()
            subprocess.run(["osascript", "-e", f"set the clipboard to «data HTML{hexdata}»"], check=True)
            return True
        if system == "Linux":
            doc = wrap_html(fragment).encode("utf-8")
            for cmd in (["wl-copy", "--type", "text/html"], ["xclip", "-selection", "clipboard", "-t", "text/html", "-i"]):
                if shutil.which(cmd[0]):
                    subprocess.run(cmd, input=doc, check=True)
                    return True
    except Exception:
        pass
    return False


def open_in_browser(fragment: str) -> bool:
    """Solution de secours : ouvre l'article dans le navigateur (Ctrl+A puis Ctrl+C)."""
    try:
        path = Path(tempfile.gettempdir()) / "supplychaindive_article.html"
        path.write_text(wrap_html(fragment), encoding="utf-8")
        return webbrowser.open(path.as_uri())
    except Exception:
        return False


def copy_rich_and_report(article: Article) -> None:
    if copy_html_to_clipboard(article.html, article.text):
        print("[✓] Article copié avec sa mise en forme (à coller dans Word, Gmail, Google Docs...).")
    elif open_in_browser(article.html):
        print("[!] Copie directe impossible sur ce système.")
        print("    L'article vient de s'ouvrir dans votre navigateur : Ctrl+A puis Ctrl+C pour le copier")
        print("    avec sa mise en forme. (Linux : installer xclip ou wl-clipboard permet la copie directe.)")
    else:
        print("[!] Copie impossible.")


def copy_text_and_report(article: Article) -> None:
    if copy_plain_text(article.text):
        print("[✓] Article copié en texte brut.")
    else:
        print("[!] Copie impossible. Installez pyperclip (pip install pyperclip).")


# --------------------------------------------------------------------------- #
# Programme principal
# --------------------------------------------------------------------------- #
def normalize_url(raw: str) -> str:
    raw = raw.strip()
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    return raw


def run(url: str) -> Article | None:
    try:
        article = fetch_article(normalize_url(url))
    except requests.RequestException as exc:
        print(f"[!] Impossible de charger l'article : {exc}")
        return None
    print("\n" + article.text + "\n")
    return article


def main() -> None:
    try:  # évite les erreurs d'encodage dans les consoles Windows
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser(description="Extraction d'un article Supply Chain Dive")
    ap.add_argument("url", nargs="?", help="Lien de l'article (sinon saisie interactive)")
    ap.add_argument("--copy", action="store_true", help="Copier l'article avec sa mise en forme")
    ap.add_argument("--copy-text", action="store_true", help="Copier l'article en texte brut")
    args = ap.parse_args()

    if args.url:
        article = run(args.url)
        if article and args.copy:
            copy_rich_and_report(article)
        if article and args.copy_text:
            copy_text_and_report(article)
        return

    last: Article | None = None
    while True:
        try:
            raw = input("Lien de l'article ('c' = copier avec mise en forme, 't' = copier en texte brut, 'q' = quitter) : ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        cmd = raw.lower()
        if cmd in ("q", "quit", "exit"):
            print("Au revoir !")
            break
        if cmd in ("c", "t"):
            if not last:
                print("[!] Aucun article à copier.")
            elif cmd == "c":
                copy_rich_and_report(last)
            else:
                copy_text_and_report(last)
            continue
        if raw:
            article = run(raw)
            if article:
                last = article


if __name__ == "__main__":
    main()
