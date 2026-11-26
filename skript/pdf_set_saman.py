"""Set saman forside (s. 1), blank side (s. 2), forord (s. 3), innhaldsliste og tekstsidene til éin PDF.

Les pdf_test/_render.json (frå pdf_render.py) og skript/Forord.md (kan redigerast; utan fila blir
det ikkje noko forord). Bruk: python pdf_set_saman.py <utfil.pdf>
"""
import datetime, html, json, os, sys
import markdown
import pymupdf
from playwright.sync_api import sync_playwright
# Stiar: skriptet ligg i <prosjekt>/skript/. Kjeldefiler og resultat ligg i <prosjekt>/,
# mellomdata (nedlasta tekst, historikk, PDF-mellomfiler) i <prosjekt>/mellomdata/.
SKRIPT = os.path.dirname(os.path.abspath(__file__))
PROSJEKT = os.path.dirname(SKRIPT)
SCR = os.path.join(PROSJEKT, "mellomdata")


TMP = os.path.join(SCR, "pdf_test")
UT = sys.argv[1]
MARG = {"top": "18mm", "bottom": "20mm", "left": "18mm", "right": "18mm"}
FORORD = os.path.join(SKRIPT, "Forord.md")
# Baksida: linjene blir sette opp som på forsida (1. linje som tittelen, 2. som undertittelen,
# resten som linja under logoen), med same skrift og fargar.
BAKSIDE = ["Bylovsjubileet 1276–2026", "Universitetet i Bergen", "2026"]

JSN = os.path.join(TMP, "_render.json")
# Datoen sidene vart henta = då pdf_render.py sist skreiv _render.json
HENTA = datetime.date.fromtimestamp(os.path.getmtime(JSN)).isoformat()
R = json.load(open(JSN, encoding="utf-8"))
# _render.json lagrar absolutte stiar. Finn filene ut frå filnamnet i pdf_test/, så det
# framleis verkar om prosjektmappa er flytta.
for r in R:
    for k in ("fil", "forside_fil"):
        if r.get(k):
            r[k] = os.path.join(TMP, os.path.basename(r[k]))
# Forsida (s. 1) er berre hovudbiletet frå framsida; sjølve framsida er første tekstside.
forside = [r for r in R if r["nivå"] == 0]
assert len(forside) == 1 and forside[0].get("forside_fil"), "manglar framsida / forsidebiletet"
forside = forside[0]
assert pymupdf.open(forside["forside_fil"]).page_count == 1
innhald = R
feil = [r for r in R if r.get("feil")]
assert not feil, "sider som ikkje vart teikna opp: " + ", ".join(f"{r['nr']} {r['tittel']}" for r in feil)


forord_sider = 0  # blir sett når forordet er teikna opp


def startsider(toc_sider):
    """Startside for kvar post; overskrifter utan side får sida til neste post med fil."""
    s, side = {}, 3 + forord_sider + toc_sider
    for r in innhald:
        if r["fil"]:
            s[r["nr"]] = side
            side += r["sider"]
    neste = None
    for r in reversed(innhald):
        if r["fil"]:
            neste = s[r["nr"]]
        else:
            s[r["nr"]] = neste
    return s


# Forfattar frå ordna-fila
import csv
CSV = os.path.join(PROSJEKT, "ordna/bylovsjubileet_artiklar_ordna.csv")
FORF = {int(r["rekkjefølgje"]): r["forfatter"] for r in csv.DictReader(open(CSV, encoding="utf-8-sig"), delimiter=";")}

CSS = """
html, body { background: #fff !important; }
body > *:not(#toc):not(#forord):not(#bakside) { display: none !important; }
#forord { padding: 0; margin: 0; color: #222; line-height: 1.6; }
#forord h1 { font-size: 2.2em; font-weight: 600; margin: 0 0 1em 0; color: var(--h1farge); font-family: var(--h1font); }
#forord h2 { font-size: 1.3em; font-weight: 600; margin: 1.4em 0 .5em 0; }
#forord p { margin: 0 0 .9em 0; }
#forord ol, #forord ul { margin: 0 0 .9em 0; padding-left: 1.6em; }
#forord ol { list-style: decimal; }
#forord ul { list-style: disc; }
#forord li { margin-bottom: .5em; }
#forord a { text-decoration: underline; }
#toc { padding: 0; margin: 0; color: #222; }
#toc h1 { font-size: 2.2em; font-weight: 600; margin: 0 0 1.2em 0; color: var(--h1farge); font-family: var(--h1font); }
#toc ol { list-style: none; padding: 0; margin: 0; }
#toc li { display: flex; align-items: baseline; gap: .4em; margin: 0 0 .55em 0; break-inside: avoid; }
#toc li .t { flex: 0 1 auto; }
#toc li .f { font-style: italic; color: #666; font-size: .9em; }
#toc li .d { flex: 1 1 auto; border-bottom: 1px dotted #999; transform: translateY(-.3em); min-width: 1.5em; }
#toc li .p { flex: 0 0 auto; min-width: 1.6em; text-align: right; }
#toc li.n0 { font-weight: 600; font-size: 1.15em; }
#toc li.n1 { font-weight: 600; margin-top: 1em; font-size: 1.08em; }
#toc li.n2 { padding-left: 1.6em; }
#toc li.n3 { padding-left: 3.2em; }
#toc li.overskrift { font-weight: 600; font-style: normal; margin-top: .6em; }
#toc li.overskrift .d, #toc li.overskrift .p { visibility: hidden; }
#toc .kjelde { margin-top: 2.5em; font-size: .85em; color: #666; border-top: 1px solid #ddd; padding-top: .8em; }
/* Tett variant for lange lister: mindre luft mellom postane før skrifta blir krympa meir */
#toc.tett h1 { margin-bottom: .8em; }
#toc.tett li { margin-bottom: .32em; }
#toc.tett li.n1 { margin-top: .7em; }
#toc.tett li.overskrift { margin-top: .4em; }
#toc.tett .kjelde { margin-top: 1.5em; }
"""


def toc_html(sider, tett=False):
    li = []
    for r in innhald:
        klasse = f"n{r['nivå']}" + ("" if r["fil"] else " overskrift")
        f = FORF.get(r["nr"], "")
        li.append(f'<li class="{klasse}"><span class="t">{html.escape(r["tittel"])}'
                  + (f' <span class="f">– {html.escape(f)}</span>' if f else "")
                  + f'</span><span class="d"></span><span class="p">{sider[r["nr"]] if r["fil"] else ""}</span></li>')
    return (f'<div id="toc"{" class=\"tett\"" if tett else ""}><h1>Innhald</h1><ol>' + "".join(li) + "</ol>"
            f'<p class="kjelde">Utskrift av nettutstillinga <i>{html.escape(forside["tittel"])}</i>, '
            f'{html.escape(forside["url"])}, henta {HENTA}. Venstremenyen og toppramma på nettsidene er tekne bort.</p></div>')


def lag_toc(pg, sider, fil, skala=0.8, tett=False):
    pg.evaluate("h => { document.getElementById('forord')?.remove(); document.getElementById('toc')?.remove();"
                " document.body.insertAdjacentHTML('afterbegin', h); }", toc_html(sider, tett))
    pg.pdf(path=fil, format="A4", print_background=True, scale=skala, margin=MARG)
    return pymupdf.open(fil).page_count


def lag_forord(pg, fil):
    """Teikn opp skript/Forord.md (Markdown) med same skrift som nettstaden."""
    tekst = open(FORORD, encoding="utf-8").read()
    innhald_html = markdown.markdown(tekst, extensions=["extra", "sane_lists"])
    pg.evaluate("h => { document.getElementById('toc')?.remove(); document.getElementById('forord')?.remove();"
                " document.body.insertAdjacentHTML('afterbegin', h); }", f'<div id="forord">{innhald_html}</div>')
    pg.pdf(path=fil, format="A4", print_background=True, scale=0.8, margin=MARG)
    return pymupdf.open(fil).page_count


def lag_bakside(pg, fil):
    """Baksida: linjene i BAKSIDE med stilane frå toppfeltet på framsida, som på forsida."""
    st = forside.get("forside_stilar") or ["", "", ""]
    linjer = []
    for i, tekst in enumerate(BAKSIDE):
        if i == 0:
            linjer.append(f'<div style="{st[0]}font-size:30pt;line-height:1.15">{html.escape(tekst)}</div>')
        elif i == 1:
            linjer.append(f'<div style="{st[1]}font-size:19pt;line-height:1.3;margin-top:4mm">{html.escape(tekst)}</div>')
        else:
            linjer.append(f'<div style="{st[2]}font-size:14pt;margin-top:4mm">{html.escape(tekst)}</div>')
    side = ('<div id="bakside" style="width:210mm;height:296mm;box-sizing:border-box;padding:20mm 18mm;'
            'display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center">'
            + "".join(linjer) + "</div>")
    pg.add_style_tag(content="html, body { margin: 0 !important; padding: 0 !important; }")
    pg.evaluate("h => { ['toc', 'forord', 'bakside'].forEach(i => document.getElementById(i)?.remove());"
                " document.body.insertAdjacentHTML('afterbegin', h); }", side)
    pg.pdf(path=fil, format="A4", print_background=True, margin={k: "0mm" for k in MARG})
    assert pymupdf.open(fil).page_count == 1, "baksida vart meir enn éi side"


toc_fil = os.path.join(TMP, "innhald.pdf")
forord_fil = os.path.join(TMP, "forord.pdf")
bakside_fil = os.path.join(TMP, "bakside.pdf")
with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge")
    pg = b.new_page(color_scheme="light", viewport={"width": 823, "height": 1000})
    # Bruk ei artikkelside som mal, så skrifttypar og fargar blir dei same som på nettstaden.
    mal = next(r["url"] for r in innhald if r["fil"] and r["nivå"] >= 2)
    pg.goto(mal, wait_until="networkidle", timeout=120000)
    stil = pg.evaluate("() => { const h = getComputedStyle(document.querySelector('#nd-page h1')); return [h.color, h.fontFamily]; }")
    pg.add_style_tag(content=CSS.replace("var(--h1farge)", stil[0]).replace("var(--h1font)", stil[1]))
    pg.emulate_media(media="screen")
    # Forordet (s. 3 ff.) kjem før innhaldslista.
    if os.path.exists(FORORD):
        forord_sider = lag_forord(pg, forord_fil)
        print("forord:", forord_sider, "side(r)")
    # Innhaldslista skal stå på éi side åleine (etter forordet):
    # krymp ho litt om ho ikkje får plass på éi side, og bruk tettare linjeavstand før
    # skrifta blir svært lita.
    for toc_skala, tett in ((0.8, False), (0.74, False), (0.68, False), (0.62, False),
                            (0.68, True), (0.62, True), (0.56, True), (0.52, True)):
        if lag_toc(pg, startsider(1), toc_fil, toc_skala, tett) == 1:
            break
    else:
        raise SystemExit("innhaldslista får ikkje plass på éi side")
    print("innhaldsliste: skala", toc_skala, "| tett" if tett else "")
    # Baksida (siste side) – teiknast sist, sidan ho nullstiller margane på sida.
    lag_bakside(pg, bakside_fil)
    b.close()
toc_sider = pymupdf.open(toc_fil).page_count
SIDER = startsider(toc_sider)

# Set saman
ut = pymupdf.open()
ut.insert_pdf(pymupdf.open(forside["forside_fil"]))
rect = ut[0].rect
ut.new_page(width=rect.width, height=rect.height)  # side 2: blank
if forord_sider:
    ut.insert_pdf(pymupdf.open(forord_fil))  # side 3 ff.: forord
toc_forste = ut.page_count  # 0-basert indeks for første side i innhaldslista
ut.insert_pdf(pymupdf.open(toc_fil))
for r in innhald:
    if r["fil"]:
        assert ut.page_count + 1 == SIDER[r["nr"]], (r["tittel"], ut.page_count + 1, SIDER[r["nr"]])
        ut.insert_pdf(pymupdf.open(r["fil"]))

forste_tekstside = 3 + forord_sider + toc_sider
assert innhald[0]["fil"] is None or SIDER[innhald[0]["nr"]] == forste_tekstside

# Sidetal nedst på tekstsidene
for i in range(forste_tekstside - 1, ut.page_count):
    s = ut[i]
    t = str(i + 1)
    w = pymupdf.get_text_length(t, fontname="tiro", fontsize=9)
    s.insert_text(((s.rect.width - w) / 2, s.rect.height - 10 * 72 / 25.4), t,
                  fontname="tiro", fontsize=9, color=(0.35, 0.35, 0.35))

# Baksida skal vere siste side og liggje på baksida av eit ark: totalt partal sider,
# med ei blank side framfor baksida ved behov. (Ingen sidetal på desse.)
blank_for_bakside = (ut.page_count + 1) % 2 == 1
if blank_for_bakside:
    ut.new_page(width=rect.width, height=rect.height)
ut.insert_pdf(pymupdf.open(bakside_fil))
bakside_nr = ut.page_count

# Klikkbare postar i innhaldslista
for r in innhald:
    if not SIDER.get(r["nr"]):
        continue
    for k in range(toc_forste, toc_forste + toc_sider):
        treff = ut[k].search_for(r["tittel"])
        if treff:
            ut[k].insert_link({"kind": pymupdf.LINK_GOTO, "from": treff[0], "page": SIDER[r["nr"]] - 1,
                               "to": pymupdf.Point(0, 0)})
            break

# Bokmerke
bm = [[1, "Forside", 1]] + ([[1, "Forord", 3]] if forord_sider else []) + [[1, "Innhald", toc_forste + 1]]
forrige = 1
for r in innhald:
    if not SIDER.get(r["nr"]):
        continue
    niv = min(max(1, r["nivå"]), forrige + 1)
    bm.append([niv, r["tittel"], SIDER[r["nr"]]])
    forrige = niv
bm.append([1, "Bakside", bakside_nr])
ut.set_toc(bm)
ut.set_metadata({"title": forside["tittel"], "subject": f"Utskrift av {forside['url']}, henta {HENTA}",
                 "creator": "Playwright/Edge + PyMuPDF"})
os.makedirs(os.path.dirname(UT), exist_ok=True)
ut.save(UT, garbage=3, deflate=True)
print("lagra:", UT, "| sider:", ut.page_count, "| forord:", forord_sider, "side(r) | innhaldsliste:", toc_sider,
      "side(r) | første tekstside:", forste_tekstside, "| bakside: s.", bakside_nr,
      "(med blank side framfor)" if blank_for_bakside else "", "| henta:", HENTA)
for r in innhald:
    print(f"  s. {SIDER[r['nr']]!s:>3}  nivå {r['nivå']}  {r['tittel']}  ({r['sider']} s.)")
