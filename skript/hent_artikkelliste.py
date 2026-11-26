"""Hent lista over sider (tittel, forfattar, URL) i nettutstillinga https://bylovsjubileet.uib.no/.

Bygd på brukaren sitt originalskript bylovjub.py (køyrt 2026-11-25, laga bylovsjubileet_artiklar.csv).
Endringar frå originalen:
1. Lenker blir henta både frå <a href> og frå navigasjonsdataa som Next.js legg inn i sida
   ("url"/"href" i JSON-dataa). Sidene under /kreditering/ finst berre der (menyen blir laga
   med JavaScript), og vart difor ikkje funne av originalen.
2. Prefikset /no/ (standardspråket) blir teke bort, så same side ikkje kjem to gonger
   (originalen gav fire duplikat under /no/c/).
3. Tittelen er teksten i <h1> utan knappar. På sidene under /kreditering/ har overskrifta ein
   knapp med teksten «Copy Anchor Link».
4. Berre svar med Content-Type text/html blir rekna som sider.
5. Berre requests + BeautifulSoup (originalen prøvde Playwright/Chromium først, men fall
   tilbake til requests når nettlesaren mangla; resultatet er det same).
6. Resultatet blir skrive til mellomdata/ (ikkje over originalfila), og samanlikna med
   ordna/bylovsjubileet_artiklar_ordna.csv.

Bruk: python hent_artikkelliste.py [utfil.csv]
"""
from collections import deque
import csv
import os
import re
import sys
import time
from urllib.parse import urljoin, urldefrag, urlparse

import requests
from bs4 import BeautifulSoup

SKRIPT = os.path.dirname(os.path.abspath(__file__))
PROSJEKT = os.path.dirname(SKRIPT)
OUTPUT_CSV = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROSJEKT, "mellomdata", "artikkelliste_crawl.csv")
ORDNA_CSV = os.path.join(PROSJEKT, "ordna", "bylovsjubileet_artiklar_ordna.csv")

START_URL = "https://bylovsjubileet.uib.no/"
ALLOWED_HOST = "bylovsjubileet.uib.no"
MAX_PAGES = 500

HEADERS = {
    "User-Agent": "BylovsjubileetURLHenter/1.2 (Python script)"
}

SKIP_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico",
    ".pdf", ".zip", ".css", ".js", ".woff", ".woff2", ".mp4", ".mp3",
)

# Interne stiar i JSON-dataa frå Next.js, t.d. \"url\":\"/no/kreditering/litteratur\"
DATA_STI = re.compile(r'\\?"(?:url|href)\\?"\s*:\s*\\?"(/[^"\\]*)')


def normalize_url(base_url: str, href: str) -> str | None:
    """Gjer lenkja absolutt, fjernar #fragment og /no/-prefiks, og filtrerer til same domene."""
    if not href:
        return None
    href = href.strip()
    if href.startswith(("mailto:", "tel:", "javascript:", "#")):
        return None

    abs_url = urljoin(base_url, href)
    clean_url, _ = urldefrag(abs_url)
    parsed = urlparse(clean_url)

    if parsed.scheme not in {"http", "https"}:
        return None
    if parsed.netloc.lower() != ALLOWED_HOST:
        return None
    if parsed.path.lower().endswith(SKIP_EXTENSIONS):
        return None

    path = parsed.path if parsed.path == "/" else parsed.path.rstrip("/")
    # Endring 2: /no/... er same side som /... (standardspråket)
    if path == "/no":
        path = "/"
    elif path.startswith("/no/"):
        path = path[3:]
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{parsed.scheme}://{parsed.netloc.lower()}{path}{query}"


def extract_author(soup: BeautifulSoup) -> str:
    """Leitar etter forfattarnamn i <div class="text-fd-muted-foreground -mt-3 italic">."""
    author_div = soup.select_one("div.text-fd-muted-foreground.-mt-3.italic")
    if not author_div:
        author_div = soup.select_one("div.text-fd-muted-foreground.italic")
    if not author_div:
        return ""
    raw_text = " ".join(author_div.get_text(" ", strip=True).split())
    cleaned = re.sub(r"^(?:av|forfatter|forfattar)\s*:?\s+", "", raw_text, flags=re.IGNORECASE)
    return cleaned.strip()


def extract_title(soup: BeautifulSoup) -> str:
    """Endring 3: teksten i <h1> utan knappar (t.d. «Copy Anchor Link»)."""
    h1_tag = soup.find("h1")
    if h1_tag:
        for knapp in h1_tag.find_all("button"):
            knapp.decompose()
        tekst = " ".join(h1_tag.get_text(" ", strip=True).split())
        if tekst:
            return tekst
    title_tag = soup.find("title")
    return " ".join(title_tag.get_text(" ", strip=True).split()) if title_tag else ""


def extract_page_data(html: str, page_url: str) -> tuple[str, str, list[str]]:
    """Returnerer (tittel, forfattar, interne lenker)."""
    soup = BeautifulSoup(html, "html.parser")
    found: list[str] = []
    for a in soup.find_all("a", href=True):
        norm = normalize_url(page_url, a["href"])
        if norm:
            found.append(norm)
    # Endring 1: lenker i navigasjonsdataa frå Next.js
    for sti in DATA_STI.findall(html):
        norm = normalize_url(page_url, sti)
        if norm:
            found.append(norm)
    return extract_title(soup), extract_author(soup), found


def is_likely_article_url(url: str) -> bool:
    """Filtrerer bort reine rot- og språkoversikts-stiar."""
    path = urlparse(url).path.rstrip("/")
    return path not in {"", "/no", "/en"}


def crawl_site(start_url: str) -> list[dict[str, str]]:
    visited: set[str] = set()
    queued: set[str] = {start_url}
    queue: deque[str] = deque([start_url])
    rows: list[dict[str, str]] = []

    with requests.Session() as session:
        while queue and len(visited) < MAX_PAGES:
            url = queue.popleft()
            if url in visited:
                continue
            visited.add(url)
            try:
                resp = session.get(url, headers=HEADERS, timeout=30)
                resp.raise_for_status()
            except Exception as exc:
                print(f"Kunne ikkje lese {url}: {exc}")
                continue
            # Endring 4: berre HTML-sider
            if "text/html" not in resp.headers.get("Content-Type", ""):
                continue

            title, author, links = extract_page_data(resp.text, url)
            if is_likely_article_url(url):
                rows.append({"tittel": title, "forfatter": author, "url": url})

            for link in links:
                if link not in visited and link not in queued:
                    queued.add(link)
                    queue.append(link)

            if len(visited) % 10 == 0:
                print(f"Vitja {len(visited)} sider, i kø: {len(queue)}...")
            time.sleep(0.25)

    rows.sort(key=lambda r: r["url"])
    return rows


def samanlikn_med_ordna(rows: list[dict[str, str]]) -> None:
    """Endring 6: vis skilnader mot ordna-fila (som blir halden ved like for hand)."""
    if not os.path.exists(ORDNA_CSV):
        return
    ordna = {r["url"]: r for r in csv.DictReader(open(ORDNA_CSV, encoding="utf-8-sig"), delimiter=";")
             if r["url"] and r["nivå"] != "0"}
    funne = {r["url"]: r for r in rows}
    berre_crawl = sorted(set(funne) - set(ordna))
    berre_ordna = sorted(set(ordna) - set(funne))
    ulik_tittel = [(u, ordna[u]["tittel"], funne[u]["tittel"]) for u in sorted(set(funne) & set(ordna))
                   if ordna[u]["tittel"] != funne[u]["tittel"]]
    print(f"\nSamanlikning med {os.path.relpath(ORDNA_CSV, PROSJEKT)}:")
    print("  Nye sider (ikkje i ordna-fila):", berre_crawl or "ingen")
    print("  Manglar på nettstaden (berre i ordna-fila):", berre_ordna or "ingen")
    print("  Ulik tittel:", ulik_tittel or "ingen")


def main() -> None:
    start = normalize_url(START_URL, START_URL) or START_URL
    rows = crawl_site(start)
    os.makedirs(os.path.dirname(os.path.abspath(OUTPUT_CSV)), exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["tittel", "forfatter", "url"], delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Ferdig! Lagra {len(rows)} URL-ar til {OUTPUT_CSV}.")
    samanlikn_med_ordna(rows)


if __name__ == "__main__":
    main()
