#!/usr/bin/env python3
"""
Saisir le lien d'un article Air Cargo Week -> affiche :
    - le titre
    - le contenu de l'article (les puces de résumé du début en font partie),
      avec [IMAGE_N] à l'emplacement des images du milieu et [EMBED_N] à l'emplacement
      des contenus intégrés (iframe) : vidéos Vimeo / YouTube, etc.
    - à la fin, l'image principale, la liste des IMAGE_N et la liste des EMBED_N
      (avec légende / titre éventuel)

Air Cargo Week n'a pas de sous-titre : il n'est donc pas affiché.
La date et l'auteur sont ignorés. Sont aussi retirés : les pubs, les boutons de partage,
la fiche auteur, le formulaire d'abonnement, les "related articles" et les icônes
de copie ajoutées sur les images.

IMAGES
    Les vignettes WordPress (photo-768x576.jpg) sont remplacées par l'image d'origine
    (photo.jpg). Si l'image n'a pas de légende, son texte alternatif (alt) sert de légende.

PRESSE-PAPIER
    'c' : copie AVEC la mise en forme de la page (titres, gras, italique, liens,
          paragraphes, listes) -> à coller dans Word, Gmail, Google Docs, etc.
    't' : copie en texte brut (comme affiché dans le terminal).

Dépendances :
    pip install requests beautifulsoup4
    pip install pyperclip        (optionnel : uniquement pour la copie en texte brut)

Utilisation :
    python aircargoweek_article.py                         # saisie interactive
    python aircargoweek_article.py <lien>                  # un seul article
    python aircargoweek_article.py <lien> --copy           # + copie avec mise en forme
    python aircargoweek_article.py <lien> --copy-text      # + copie en texte brut
"""

import argparse
import html as htmllib
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
END_MARKERS = (
    "related articles",
    "subscribe to acw",
    "more articles by",
)

# Paragraphes ignorés (mais le contenu continue), ex : "(UPDATED 1:15 p.m. ET)"
IGNORED_PATTERNS = [
    re.compile(r"^read more\s*:", re.I),  # liens internes "Read more: ..." insérés dans le texte
    re.compile(r"^read more\s*:", re.I),  # liens "Read more: ..." vers d'autres articles
    re.compile(r"^\(\s*(update[d]?|correct(?:ed|ion)|editor.?s note)\b.*\)$", re.I),
]

SKIP_TAGS = {"script", "style", "iframe", "noscript", "link", "button", "form", "svg"}
# Blocs à ignorer : icône de copie ajoutée sur les images, pubs, partage, abonnement...
SKIP_CLASSES = {
    "acw-copy-icon",
    "emoji",
    "adspeed",
    "social-share",
    "share-buttons",
    "elementor-widget-share-buttons",
    "elementor-widget-author-box",
    "elementor-widget-divider",
    "elementor-widget-spacer",
}
TEXT_BLOCKS = {"h2", "h3", "h4", "h5", "h6"}
# Iframes conservées (vidéos, graphiques). Les iframes publicitaires n'ont pas de src : elles sont ignorées.
EMBED_HOSTS = (
    "youtube.com",
    "youtube-nocookie.com",
    "youtu.be",
    "vimeo.com",
    "datawrapper.dwcdn.net",
    "datawrapper.de",
    "flo.uri.sh",
    "flourish.studio",
    "infogram.com",
    "public.tableau.com",
    "dailymotion.com",
    "open.spotify.com",
    "w.soundcloud.com",
    "player.simplecast.com",
)
INLINE_KEPT = {"strong", "b", "em", "i", "u", "s", "strike", "sup", "sub"}  # mise en forme conservée


@dataclass
class Article:
    text: str  # version texte brut (affichée dans le terminal)
    html: str  # version HTML (mise en forme de la page) pour le presse-papier


# --------------------------------------------------------------------------- #
# Utilitaires
# --------------------------------------------------------------------------- #
def clean_image_url(url: str) -> str:
    """Retire les paramètres d'URL et le suffixe de redimensionnement WordPress (-768x576)
    pour obtenir l'image d'origine : .../photo-768x576.jpg -> .../photo.jpg"""
    p = urlsplit(url)
    path = re.sub(r"-\d+x\d+(?=\.\w+$)", "", p.path)
    return urlunsplit((p.scheme, p.netloc, path, "", ""))


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
    """URL de l'iframe si c'est un contenu intégré connu (Vimeo, YouTube...), sinon None.
    Gère src / data-src (lazy-load). Les paramètres de suivi (?h=..&dnt=1&app_id=..) sont retirés
    pour Vimeo (le paramètre h des vidéos privées est conservé)."""
    for attr in ("src", "data-src-cmplz", "data-src", "data-lazy-src"):
        value = iframe.get(attr)
        if not value or value.startswith(("data:", "about:")):
            continue
        url = urljoin(base_url, value.strip())  # gère aussi les liens "//player.vimeo.com/..."
        host = (urlsplit(url).hostname or "").lower()
        if any(host == h or host.endswith("." + h) for h in EMBED_HOSTS):
            if host.endswith("vimeo.com"):
                p = urlsplit(url)
                h = re.search(r"(?:^|&)h=(\w+)", p.query)
                url = urlunsplit((p.scheme, p.netloc, p.path, f"h={h.group(1)}" if h else "", ""))
            return url
    return None


def is_skipped(tag: Tag) -> bool:
    if tag.name in SKIP_TAGS:
        return True
    classes = tag.get("class") or []
    return any(c in SKIP_CLASSES or c.startswith("adspeed") for c in classes)


def media_in(node: Tag) -> list[Tag]:
    """Images et iframes d'un bloc, dans l'ordre du document (hors icônes de copie, emoji, pubs)."""
    found = []
    for el in node.find_all(["img", "iframe"]):
        skipped = False
        cur = el
        while cur is not None and cur is not node:
            if isinstance(cur, Tag) and cur.name != "iframe" and is_skipped(cur):
                skipped = True
                break
            cur = cur.parent
        if not skipped:
            found.append(el)
    return found


def caption_of(node: Tag) -> str:
    """Légende d'une figure / d'un bloc 'wp-caption' (vide s'il n'y en a pas)."""
    cap = node.find("figcaption") or node.select_one(".wp-caption-text")
    return clean_text(cap) if cap else ""



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
        if not url or url.lower().endswith(".svg") or any(url == u for u, _ in self.images):
            return
        self.images.append((url, caption or (img.get("alt") or "").strip()))
        placeholder = f"[IMAGE_{len(self.images)}]"
        self.blocks.append((placeholder, f"<p>{placeholder}</p>"))

    def add_embed(self, iframe: Tag, caption: str = "") -> None:
        url = embed_url(iframe, self.base_url)
        if not url or any(url == u for u, _ in self.embeds):
            return
        self.embeds.append((url, caption or (iframe.get("title") or "").strip()))
        placeholder = f"[EMBED_{len(self.embeds)}]"
        self.blocks.append((placeholder, f"<p>{placeholder}</p>"))

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

    def walk(self, node: Tag) -> None:
        for child in node.children:
            if self.stopped:
                return
            if not isinstance(child, Tag):
                continue
            if child.name == "iframe":  # seules les iframes connues (Vimeo, YouTube...) sont gardées
                if not any(is_skipped(p) for p in child.parents if isinstance(p, Tag)):
                    self.add_embed(child)
                continue
            if is_skipped(child):
                continue

            name = child.name
            classes = child.get("class") or []
            if name == "p":
                self.add_media(media_in(child))
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
            elif name == "figure" or "wp-caption" in classes:
                self.add_media(media_in(child), caption_of(child))
            elif name == "img":
                self.add_image(child)
            else:
                self.walk(child)  # div / section imbriquées


# --------------------------------------------------------------------------- #
# Construction de l'article
# --------------------------------------------------------------------------- #
def find_title(soup: BeautifulSoup) -> Tag | None:
    """Titre de l'article (pas le 'subscribe to acw for free' ni 'related articles' plus bas)."""
    crumb = soup.select_one(".jet-breadcrumbs__item-target")
    h = soup.select_one("h1.elementor-heading-title, h1.entry-title") or soup.select_one(
        "h2.elementor-heading-title"
    )
    if h and clean_text(h).lower().startswith(END_MARKERS):
        h = None
    return h or crumb or soup.find("h1")


def find_main_image(soup: BeautifulSoup, base_url: str, content: Tag | None) -> str | None:
    """Image principale : première image WordPress placée AVANT le corps de l'article
    (celles qui suivent : logo, bandeau newsletter... sont ignorées)."""
    candidates = list(reversed(content.find_all_previous("img"))) if content else soup.select(".elementor-widget-image img")
    for img in candidates:
        url = image_url(img, base_url)
        if url and not url.lower().endswith(".svg") and "wp-content/uploads" in url and not img.find_parent(
            class_=("elementor-location-header", "elementor-location-footer")
        ):
            return url
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return clean_image_url(og["content"])
    return None


def parse_article(html: str, base_url: str) -> Article:
    soup = BeautifulSoup(html, "html.parser")

    h1 = find_title(soup)
    title = clean_text(h1) if h1 else "(titre introuvable)"
    title_html = inline_html(h1, base_url) if h1 else htmllib.escape(title)

    content = soup.select_one(".elementor-widget-theme-post-content") or soup.select_one(
        "div.entry-content, article"
    )
    main_image_url = find_main_image(soup, base_url, content)
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
    text_out = [title, ""]
    text_out.append("\n\n".join(t for t, _ in extractor.blocks))
    if image_lines:
        text_out += ["", SEPARATOR, *image_lines, SEPARATOR]

    # --- version HTML (mise en forme de la page) ---
    html_out = [f"<h1>{title_html}</h1>"]
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
        path = Path(tempfile.gettempdir()) / "aircargoweek_article.html"
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

    ap = argparse.ArgumentParser(description="Extraction d'un article Air Cargo Week")
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
