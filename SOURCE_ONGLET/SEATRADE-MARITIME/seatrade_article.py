#!/usr/bin/env python3
"""
Saisir le lien d'un article Seatrade Maritime -> affiche :
    - le titre
    - le sous-titre (résumé placé sous le titre)
    - le contenu de l'article, avec [IMAGE_N] à l'emplacement des images du milieu
      et [EMBED_N] à l'emplacement des contenus intégrés : vidéo YouTube (articles "Video"),
      lecteur audio (articles "Podcast"), etc. Le lecteur vidéo / audio, qui est placé
      au-dessus du texte sur le site, apparaît donc en [EMBED_1] au début du contenu.
    - les tableaux (ex. listes de navires) sont insérés dans le texte : lignes "a | b | c"
      en texte brut, vrai tableau HTML pour la copie avec mise en forme
    - à la fin, l'image principale, la liste des IMAGE_N et la liste des EMBED_N
      (avec légende / titre éventuel)

La date et l'auteur sont ignorés. Sont aussi retirés : les liens "Related: ..." insérés
dans le texte, les boutons de partage, la fiche auteur, l'inscription à la newsletter,
les recommandations ("Iris"), la colonne latérale et tout ce qui suit le corps de l'article.

Dépendances :
    pip install requests beautifulsoup4
    pip install pyperclip        (optionnel : uniquement pour la copie en texte brut)

PRESSE-PAPIER
    'c' : copie AVEC la mise en forme de la page (titres, gras, italique, liens,
          paragraphes, listes, tableaux) -> à coller dans Word, Gmail, Google Docs, etc.
    't' : copie en texte brut (comme affiché dans le terminal).

Utilisation :
    python seatrade_article.py                         # saisie interactive
    python seatrade_article.py <lien>                  # un seul article
    python seatrade_article.py <lien> --copy           # + copie avec mise en forme
    python seatrade_article.py <lien> --copy-text      # + copie en texte brut
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
)

# Paragraphes ignorés (mais le contenu continue)
IGNORED_PATTERNS = [
    re.compile(r"^related\s*:", re.I),  # filet "Related: ..." (aussi retiré par sa classe)
    re.compile(r"^\(\s*(update[d]?|correct(?:ed|ion)|editor.?s note)\b.*\)$", re.I),
]

SKIP_TAGS = {"script", "style", "iframe", "noscript", "link", "button", "form", "svg"}
# Blocs à ignorer : "Related", partage, icônes, tri des tableaux, auteur, newsletter, recommandations...
SKIP_CLASSES = {
    "RelatedArticle",
    "SocialShare",
    "ContentTable-SortButton",
    "ContentTable-SortIcon",
    "BaseMaterialIcon",
    "BasicList-ListIcon",
    "ContributorSummary",
    "Iris-Rec",
    "ArticleBase-IirisRecommendation",
    "ArticleBase-More",
    "ArticleBase-Keywords",
    "ArticleBase-Footer",
    "ArticleBase-SponsoredWrapper",
    "TwoColumnLayout-Sidebar",
}
TEXT_BLOCKS = {"h2", "h3", "h4", "h5", "h6"}
# Contenus intégrés conservés (iframe ou balise <youtube-video>)
EMBED_HOSTS = (
    "youtube.com",
    "youtube-nocookie.com",
    "youtu.be",
    "vimeo.com",
    "captivate.fm",
    "spotify.com",
    "soundcloud.com",
    "simplecast.com",
    "podbean.com",
    "buzzsprout.com",
    "libsyn.com",
    "anchor.fm",
    "datawrapper.dwcdn.net",
    "flo.uri.sh",
    "flourish.studio",
    "infogram.com",
    "public.tableau.com",
)
INLINE_KEPT = {"strong", "b", "em", "i", "u", "s", "strike", "sup", "sub"}  # mise en forme conservée
# Mise en forme portée par des classes (<span class="ContentText-BodyTextChunk_bold">)
CLASS_FORMATS = {
    "ContentText-BodyTextChunk_bold": "strong",
    "ContentText-BodyTextChunk_italic": "em",
    "ContentText-BodyTextChunk_underline": "u",
}


@dataclass
class Article:
    text: str  # version texte brut (affichée dans le terminal)
    html: str  # version HTML (mise en forme de la page) pour le presse-papier


# --------------------------------------------------------------------------- #
# Utilitaires
# --------------------------------------------------------------------------- #
def clean_image_url(url: str) -> str:
    """Retire les paramètres de redimensionnement (?width=1280&auto=webp&quality=80...)."""
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



def is_skipped(tag: Tag) -> bool:
    if tag.name in SKIP_TAGS:
        return True
    return any(c in SKIP_CLASSES for c in (tag.get("class") or []))


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
        fmt = next((CLASS_FORMATS[c] for c in (child.get("class") or []) if c in CLASS_FORMATS), None)
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


def table_blocks(table: Tag, base_url: str) -> tuple[str, str] | None:
    """(texte brut, html) d'un tableau : 1re ligne = en-tête."""
    rows = []
    for tr in table.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        if cells:
            rows.append(
                [
                    (clean_text_skipping(c).replace("\n", " "), inline_html(c, base_url), c.name == "th")
                    for c in cells
                ]
            )
    rows = [r for r in rows if any(t for t, _, _ in r)]
    if not rows:
        return None
    plain = "\n".join(" | ".join(t for t, _, _ in r) for r in rows)
    out = '<table border="1" cellpadding="4" cellspacing="0">'
    for r in rows:
        out += "<tr>" + "".join(f"<{'th' if th else 'td'}>{h}</{'th' if th else 'td'}>" for _, h, th in r) + "</tr>"
    out += "</table>"
    return plain, out


# --------------------------------------------------------------------------- #
# Extraction du contenu
# --------------------------------------------------------------------------- #
class ContentExtractor:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.blocks: list[tuple[str, str]] = []  # (texte brut, html)
        self.images: list[tuple[str, str]] = []  # (url, légende)
        self.embeds: list[tuple[str, str]] = []  # (url, légende / titre)
        self.stopped = False

    def add_image(self, img: Tag, caption: str = "") -> None:
        url = image_url(img, self.base_url)
        if not url or any(url == u for u, _ in self.images):
            return
        self.images.append((url, caption or (img.get("alt") or "").strip()))
        placeholder = f"[IMAGE_{len(self.images)}]"
        self.blocks.append((placeholder, f"<p>{placeholder}</p>"))

    def add_embed(self, el: Tag, caption: str = "") -> None:
        url = embed_url(el, self.base_url)
        if not url or any(url == u for u, _ in self.embeds):
            return
        self.embeds.append((url, caption or (el.get("title") or el.get("aria-label") or "").strip()))
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

    def walk(self, node: Tag) -> None:
        for child in node.children:
            if self.stopped:
                return
            if not isinstance(child, Tag) or is_skipped(child):
                continue

            name = child.name
            classes = child.get("class") or []
            if name in ("iframe", "youtube-video"):
                self.add_embed(child)
            elif name == "p":
                for m in child.find_all(["img", "iframe", "youtube-video"]):
                    self.add_image(m) if m.name == "img" else self.add_embed(m)
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
            elif name == "table":
                tb = table_blocks(child, self.base_url)
                if tb:
                    self.blocks.append(tb)
            elif name == "figure" or "CaptionedContent" in classes:
                cap = child.select_one(".CaptionedContent-Caption, figcaption")
                for m in child.find_all(["img", "iframe", "youtube-video"]):
                    self.add_image(m, clean_text_skipping(cap) if cap else "") if m.name == "img" else self.add_embed(m)
            elif name == "img":
                self.add_image(child)
            else:
                self.walk(child)  # div / section imbriquées (Table-ScrollableWrapper, BasicList...)


# --------------------------------------------------------------------------- #
# Construction de l'article
# --------------------------------------------------------------------------- #
def parse_article(html: str, base_url: str) -> Article:
    soup = BeautifulSoup(html, "html.parser")

    h1 = soup.select_one(".ArticleBase-HeaderTitle h1, h1")
    title = clean_text(h1) if h1 else "(titre introuvable)"
    title_html = inline_html(h1, base_url) if h1 else htmllib.escape(title)

    sub = soup.select_one(".ArticleBase-HeaderSummary")
    subtitle = clean_text(sub) if sub else ""
    subtitle_html = inline_html(sub, base_url) if sub else ""

    # Image principale (absente des articles vidéo / podcast : le lecteur est alors en EMBED_1)
    feat = soup.select_one("img.ArticleBase-FeaturedImage")
    main_image_url = image_url(feat, base_url) if feat else None
    if not main_image_url:
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            main_image_url = clean_image_url(og["content"])

    extractor = ContentExtractor(base_url)

    # Lecteur vidéo (YouTube) / audio (podcast) : posé hors du corps du texte, on le met en tête du contenu
    for media in soup.select(".ArticleVideo-Media, .ArticlePodcast-Media"):
        for el in media.find_all(["iframe", "youtube-video"]):
            extractor.add_embed(el)

    content = soup.select_one(".ArticleBase-BodyContent .ContentModule-Wrapper") or soup.select_one(
        ".ArticleBase-BodyContent"
    )
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
        path = Path(tempfile.gettempdir()) / "seatrade_article.html"
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

    ap = argparse.ArgumentParser(description="Extraction d'un article Seatrade Maritime")
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
