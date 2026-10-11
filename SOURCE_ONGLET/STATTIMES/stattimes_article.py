#!/usr/bin/env python3
"""
Saisir le lien d'un article STAT Times -> affiche :
    - le titre
    - le sous-titre (chapô placé sous le titre)
    - le contenu de l'article, avec [IMAGE_N] à l'emplacement des images du milieu
      et [EMBED_N] à l'emplacement des contenus intégrés (iframe YouTube, etc.)
    - à la fin, l'image principale, la liste des IMAGE_N et la liste des EMBED_N
      (avec légende / titre éventuel)

La date et l'auteur sont ignorés. Sont aussi retirés : les pubs, les liens "Also Read - ...",
les boutons de partage, les tags, la fiche auteur, le bandeau WhatsApp, les commentaires.

IMAGES
    Les images du milieu sont dans des blocs "image-and-caption-wrapper" : la légende
    (ou, à défaut, l'attribut title de l'image) est donnée après l'URL.
    Certaines images sont servies par une adresse dynamique (.../RDESController?...&uid=...) :
    son paramètre d'URL est conservé, car il identifie l'image.

PRESSE-PAPIER
    'c' : copie AVEC la mise en forme de la page (titres, gras, italique, liens,
          paragraphes, listes) -> à coller dans Word, Gmail, Google Docs, etc.
    't' : copie en texte brut (comme affiché dans le terminal).

Dépendances :
    pip install requests beautifulsoup4
    pip install pyperclip        (optionnel : uniquement pour la copie en texte brut)

Utilisation :
    python stattimes_article.py                         # saisie interactive
    python stattimes_article.py <lien>                  # un seul article
    python stattimes_article.py <lien> --copy           # + copie avec mise en forme
    python stattimes_article.py <lien> --copy-text      # + copie en texte brut
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
    "more articles by",
    "click here for more",
    "also read",
)

# Paragraphes ignorés (mais le contenu continue)
IGNORED_PATTERNS = [
    re.compile(r"^\(\s*(update[d]?|correct(?:ed|ion)|editor.?s note)\b.*\)$", re.I),
]

SKIP_TAGS = {"script", "style", "iframe", "noscript", "link", "button", "form", "svg"}
# Blocs à ignorer : pubs, "Also Read", partage, tags, auteur, commentaires...
SKIP_CLASSES = {
    "read-this-also-wrap",
    "read-this-also",
    "also-read-media-wrap",
    "ads_common_inside_post",
    "inside-post-ad",
    "inside-post-ad-before",
    "inside-post-ad-before-before",
    "inside-post-ad-after",
    "filler-ad-unit-inside-post",
    "in-image-ad-wrap",
    "to-be-async-loaded-ad",
    "social-share-on-article",
    "ind-social-wrapper",
    "entry-bottom",
    "author-credit-blocks-after-article",
    "bookmark-btn",
}
SKIP_CLASS_PREFIXES = ("inside-post-ad", "left_level", "ad-")
TEXT_BLOCKS = {"h2", "h3", "h4", "h5", "h6"}
# Contenus intégrés conservés (iframes)
EMBED_HOSTS = (
    "youtube.com",
    "youtube-nocookie.com",
    "youtu.be",
    "vimeo.com",
    "datawrapper.dwcdn.net",
    "flo.uri.sh",
    "flourish.studio",
    "infogram.com",
    "public.tableau.com",
    "open.spotify.com",
    "w.soundcloud.com",
    "dailymotion.com",
)
INLINE_KEPT = {"strong", "b", "em", "i", "u", "s", "strike", "sup", "sub"}  # mise en forme conservée


@dataclass
class Article:
    text: str  # version texte brut (affichée dans le terminal)
    html: str  # version HTML (mise en forme de la page) pour le presse-papier
    source: str = ""  # HTML brut reçu du site (commande 'h' : l'enregistrer pour diagnostic)


# --------------------------------------------------------------------------- #
# Utilitaires
# --------------------------------------------------------------------------- #
IMAGE_EXT_RE = re.compile(r"\.(?:jpe?g|png|webp|gif|avif|svg)$", re.I)


def clean_image_url(url: str) -> str:
    """Retire les paramètres d'URL des images à adresse "fichier" (.webp?x=1 -> .webp).
    Les adresses dynamiques (.../RDESController?command=rdm.Picture&uid=...) sont gardées telles
    quelles : leur paramètre identifie l'image."""
    p = urlsplit(url)
    if IMAGE_EXT_RE.search(p.path):
        return urlunsplit((p.scheme, p.netloc, p.path, "", ""))
    return url


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




def is_skipped(tag: Tag) -> bool:
    if tag.name in SKIP_TAGS:
        return True
    classes = tag.get("class") or []
    return any(c in SKIP_CLASSES or c.startswith(SKIP_CLASS_PREFIXES) for c in classes) or tag.get("id", "").startswith(
        ("inside_post_content_ad", "left_level", "IN_IMAGE_AD")
    )


def clean_text_skipping(tag: Tag) -> str:
    """Comme clean_text, mais sans le texte des blocs ignorés (icônes, boutons de tri...)."""
    parts = []

    def rec(node: Tag) -> None:
        for ch in node.children:
            if isinstance(ch, Comment):
                continue
            if isinstance(ch, NavigableString):
                parts.append(str(ch))
            elif isinstance(ch, Tag) and not is_skipped(ch):
                if ch.name == "br":
                    parts.append("\n")
                else:
                    rec(ch)

    rec(tag)
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
        fmt = None
        if child.name == "a" and child.get("href") and inner.strip():
            href = htmllib.escape(urljoin(base_url, child["href"]), quote=True)
            parts.append(f'<a href="{href}">{inner}</a>')
        elif (fmt or child.name in INLINE_KEPT) and inner.strip():
            tag = fmt or child.name
            parts.append(f"<{tag}>{inner}</{tag}>")
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



def embed_url(el: Tag, base_url: str) -> str | None:
    """URL d'un contenu intégré connu (iframe ou <youtube-video>), sinon None. Gère src / data-src."""
    for attr in ("src", "data-src", "data-lazy-src"):
        value = el.get(attr)
        if not value or value.startswith(("data:", "about:")):
            continue
        url = urljoin(base_url, value.strip())
        host = (urlsplit(url).hostname or "").lower()
        if any(host == h or host.endswith("." + h) for h in EMBED_HOSTS):
            return url
    return None



def embed_url(el: Tag, base_url: str) -> str | None:
    """URL d'un contenu intégré connu (iframe), sinon None. Gère src / data-src et les liens
    "//www.youtube.com/embed/ID?rand=..." : le paramètre de suivi est retiré pour YouTube."""
    for attr in ("src", "data-src", "data-lazy-src"):
        value = el.get(attr)
        if not value or value.startswith(("data:", "about:")):
            continue
        url = urljoin(base_url, value.strip())
        p = urlsplit(url)
        host = (p.hostname or "").lower()
        if any(host == h or host.endswith("." + h) for h in EMBED_HOSTS):
            if "youtube" in host or host == "youtu.be":
                url = urlunsplit((p.scheme, p.netloc, p.path, "", ""))
            return url
    return None


def caption_of(node: Tag, img: Tag | None = None) -> str:
    """Légende d'un bloc image (.image_caption / figcaption), sinon attribut title de l'image."""
    cap = node.select_one(".image_caption, .inside_editor_caption, figcaption")
    text = clean_text_skipping(cap) if cap else ""
    if not text and img is not None:
        text = (img.get("title") or img.get("alt") or "").strip()
    return text


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
        self.images.append((url, caption or (img.get("title") or "").strip()))
        placeholder = f"[IMAGE_{len(self.images)}]"
        self.blocks.append((placeholder, f"<p>{placeholder}</p>"))

    def add_embed(self, el: Tag, caption: str = "") -> None:
        url = embed_url(el, self.base_url)
        if not url or any(url == u for u, _ in self.embeds):
            return
        self.embeds.append((url, caption or (el.get("title") or "").strip()))
        placeholder = f"[EMBED_{len(self.embeds)}]"
        self.blocks.append((placeholder, f"<p>{placeholder}</p>"))

    def add_text(self, text: str, html_block: str) -> None:
        """Ajoute un bloc, sauf s'il est ignoré ; déclenche l'arrêt sur un marqueur de fin."""
        if text.lower().startswith(END_MARKERS):
            self.stopped = True
            return
        if not text or any(p.match(text) for p in IGNORED_PATTERNS):
            return
        self.blocks.append((text, html_block))

    def add_media_block(self, node: Tag) -> None:
        """Bloc contenant image(s) / iframe(s) (+ légende)."""
        medias = []
        for m in node.find_all(["img", "iframe"]):
            skipped, cur = False, m
            while cur is not None and cur is not node:  # on ne regarde que les blocs DANS node (pas ses ancêtres)
                if isinstance(cur, Tag) and cur.name != "iframe" and is_skipped(cur):
                    skipped = True
                    break
                cur = cur.parent
            if not skipped:
                medias.append(m)
        for m in medias:
            if m.name == "img":
                self.add_image(m, caption_of(node, m) if len(medias) == 1 else "")
            else:
                self.add_embed(m)

    def walk(self, node: Tag) -> None:
        for child in node.children:
            if self.stopped:
                return
            if not isinstance(child, Tag) or is_skipped(child):
                continue

            name = child.name
            classes = child.get("class") or []
            if name == "iframe":
                self.add_embed(child)
            elif name == "p":
                self.add_media_block(child)
                self.add_text(clean_text_skipping(child), f"<p>{inline_html(child, self.base_url)}</p>")
            elif name in TEXT_BLOCKS:
                self.add_text(clean_text_skipping(child), f"<{name}>{inline_html(child, self.base_url)}</{name}>")
            elif name == "blockquote":
                self.add_text(clean_text_skipping(child), f"<blockquote>{inline_html(child, self.base_url)}</blockquote>")
            elif name in ("ul", "ol"):
                lis = child.find_all("li", recursive=False)
                texts = [clean_text_skipping(li) for li in lis]
                if any(texts):
                    plain = "\n".join(f"- {t}" for t in texts if t)
                    items = "".join(f"<li>{inline_html(li, self.base_url)}</li>" for li, t in zip(lis, texts) if t)
                    self.blocks.append((plain, f"<{name}>{items}</{name}>"))
            elif name == "figure" or "image-and-caption-wrapper" in classes:
                self.add_media_block(child)
            elif name == "img":
                self.add_image(child)
            else:
                self.walk(child)  # div / section imbriquées


# --------------------------------------------------------------------------- #
# Construction de l'article
# --------------------------------------------------------------------------- #
def parse_article(html: str, base_url: str) -> Article:
    soup = BeautifulSoup(html, "html.parser")

    h1 = soup.select_one("h1.entry-title") or soup.find("h1")
    title = clean_text(h1) if h1 else "(titre introuvable)"
    title_html = inline_html(h1, base_url) if h1 else htmllib.escape(title)

    sub = soup.select_one("h2.excerpt, .sub-heading")
    subtitle = clean_text(sub) if sub else ""
    subtitle_html = inline_html(sub, base_url) if sub else ""

    # Image principale : grande image sous le titre (figure.image)
    main = soup.select_one("figure.image img")
    main_image_url = image_url(main, base_url) if main else None
    if not main_image_url:
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            main_image_url = clean_image_url(og["content"])

    content = (
        soup.select_one(".entry-main-content")
        or soup.select_one(".details-content-story")
        or soup.select_one(".story_content")
    )
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
    article = parse_article(resp.text, url)
    article.source = resp.text
    return article


def save_source(article: Article) -> None:
    """Enregistre le HTML brut reçu du site (pour voir ce que le script reçoit réellement)."""
    path = Path.cwd() / "stattimes_page_recue.html"
    path.write_text(article.source, encoding="utf-8")
    n_img = len(re.findall(r"<img\b", article.source))
    n_ifr = len(re.findall(r"<iframe\b", article.source))
    print(f"[✓] HTML reçu enregistré dans : {path}  ({len(article.source)} caractères, {n_img} <img>, {n_ifr} <iframe>)")


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
        path = Path(tempfile.gettempdir()) / "stattimes_article.html"
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

    ap = argparse.ArgumentParser(description="Extraction d'un article STAT Times (v3)")
    ap.add_argument("url", nargs="?", help="Lien de l'article (sinon saisie interactive)")
    ap.add_argument("--copy", action="store_true", help="Copier l'article avec sa mise en forme")
    ap.add_argument("--copy-text", action="store_true", help="Copier l'article en texte brut")
    ap.add_argument("--save-html", action="store_true", help="Enregistrer le HTML brut reçu (diagnostic)")
    args = ap.parse_args()

    if args.url:
        article = run(args.url)
        if article and args.copy:
            copy_rich_and_report(article)
        if article and args.save_html:
            save_source(article)
        if article and args.copy_text:
            copy_text_and_report(article)
        return

    last: Article | None = None
    while True:
        try:
            raw = input("Lien de l'article ('c' = copier avec mise en forme, 't' = copier en texte brut, 'h' = enregistrer le HTML reçu, 'q' = quitter) : ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        cmd = raw.lower()
        if cmd in ("q", "quit", "exit"):
            print("Au revoir !")
            break
        if cmd == "h":
            if last:
                save_source(last)
            else:
                print("[!] Aucun article chargé.")
            continue
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
