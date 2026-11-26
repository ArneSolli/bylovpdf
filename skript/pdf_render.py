"""Teikn opp hovudinnhaldet (utan venstremeny og toppramme) for sidene i ordna-fila til PDF.

Bruk: python pdf_render.py <første rekkjefølgje> <siste rekkjefølgje>
Resultat: pdf_test/side_<nr>.pdf, pdf_test/forside_bilete.pdf og pdf_test/_render.json
"""
import csv, json, os, sys, traceback
import pymupdf
from playwright.sync_api import sync_playwright
# Stiar: skriptet ligg i <prosjekt>/skript/. Kjeldefiler og resultat ligg i <prosjekt>/,
# mellomdata (nedlasta tekst, historikk, PDF-mellomfiler) i <prosjekt>/mellomdata/.
SKRIPT = os.path.dirname(os.path.abspath(__file__))
PROSJEKT = os.path.dirname(SKRIPT)
SCR = os.path.join(PROSJEKT, "mellomdata")


SRC = os.path.join(PROSJEKT, "ordna/bylovsjubileet_artiklar_ordna.csv")
OUT = os.path.join(SCR, "pdf_test")
os.makedirs(OUT, exist_ok=True)

FRA, TIL = int(sys.argv[1]), int(sys.argv[2])

# A4 med margar; 96 px per tomme
MM = 96 / 25.4
MARG = {"top": 18, "bottom": 20, "left": 18, "right": 18}  # mm
BREI_PX = (210 - MARG["left"] - MARG["right"]) * MM
SKALA = 0.8  # gjev layoutbreidd ~820 px, dvs. «md»-oppsettet til nettstaden (≥ 768 px)
# Figurar (bilete, kart, video) skal ikkje vere høgare enn 66 % av A4-høgda (297 mm).
MAKS_FIGUR_MM = 0.66 * 297
MAKS_FIGUR_PX = MAKS_FIGUR_MM * MM / SKALA  # i layout-px før skalering

FORSIDE_OVER = ["Bylovsjubileet 1276–2026", "Magnus Lagabøtes Bylov i 750 år"]
FORSIDE_UNDER = ["Digital utstilling ved Universitetet i Bergen", "https://bylovsjubileet.uib.no/"]

CSS_FELLES = """
html, body { background: #fff !important; }
a.sr-only, #nd-toc-placeholder, #nd-toc, #nd-tocnav { display: none !important; }
"""
# Artikkelsider: skjul toppramma (#nd-subnav) og venstremenyen (#nd-sidebar med omslag),
# og navigasjon/kreditering nedst i artikkelen.
CSS_ARTIKKEL = CSS_FELLES + """
#nd-subnav, #nd-nav, #nd-sidebar, [data-toc-popover], [data-sidebar-placeholder] { display: none !important; }
div:has(> #nd-sidebar) { display: none !important; }
#nd-notebook-layout, #nd-notebook-layout > main { display: block !important; min-height: 0 !important; }
#nd-page { padding: 0 !important; max-width: none !important; }
#nd-page > footer, #nd-page > div[class*="@container"] { display: none !important; }
img, figure { break-inside: avoid; }
h1, h2, h3 { break-after: avoid; }
/* Biletrader (md:flex-row med boksar som har fast breidd berre på brei skjerm, lg:w-…):
   del breidda likt, slik nettstaden gjer på brei skjerm */
#nd-page .md\\:flex-row > [class*="lg:w-"] { flex: 1 1 0 !important; min-width: 0 !important; }
"""
# Framsida som tekstside: skjul toppmenyen (#nd-nav), behald resten.
CSS_FRAMSIDE = CSS_FELLES + """
#nd-nav { display: none !important; }
#nd-home-layout, .min-h-screen { min-height: 0 !important; }
footer { margin-bottom: 0 !important; }
"""
# Andre sider med same oppsett som framsida (t.d. /kreditering/…): skjul toppmenyen og
# botnfeltet med kreditering, som på artikkelsidene.
CSS_HEIMSIDE = CSS_FRAMSIDE + """
#nd-home-layout > footer, main > footer { display: none !important; }
img, figure { break-inside: avoid; }
h1, h2, h3 { break-after: avoid; }
"""

JS_BILETE = """
async () => {
  document.querySelectorAll('img').forEach(i => { i.loading = 'eager'; i.decoding = 'sync'; });
  for (let y = 0; y < document.body.scrollHeight; y += 400) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); }
  window.scrollTo(0, 0);
  const alle = Promise.all([...document.images].map(i => i.complete ? null : new Promise(r => { i.onload = i.onerror = r; })));
  await Promise.race([alle, new Promise(r => setTimeout(r, 30000))]);
  return [...document.images].filter(i => i.getBoundingClientRect().width > 0 && !i.naturalWidth).map(i => i.src);
}
"""

# YouTube-ramer blir ikkje teikna i PDF (berre ei tom ramme): byt dei ut med førehandsbiletet
# til videoen og ein bilettekst med klikkbar lenke.
JS_VIDEO = r"""
() => {
  const ut = [];
  document.querySelectorAll('main iframe').forEach(f => {
    const m = (f.src || '').match(/youtube(?:-nocookie)?\.com\/embed\/([\w-]{6,})/);
    if (!m) return;
    const id = m[1], lenke = 'https://www.youtube.com/watch?v=' + id, tittel = f.title || 'Video';
    const fig = document.createElement('figure');
    fig.style.cssText = 'margin:1em auto;text-align:center;break-inside:avoid;max-width:640px';
    fig.innerHTML = `
      <a href="${lenke}" style="display:block;position:relative">
        <img alt="${tittel}" src="https://i.ytimg.com/vi/${id}/maxresdefault.jpg"
             onerror="this.onerror=null;this.src='https://i.ytimg.com/vi/${id}/hqdefault.jpg'"
             style="width:100%;display:block;border-radius:8px">
        <span style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:68px;height:48px;
              background:rgba(204,0,0,.9);border-radius:12px;display:flex;align-items:center;justify-content:center">
          <span style="width:0;height:0;border-left:20px solid #fff;border-top:12px solid transparent;
                border-bottom:12px solid transparent;margin-left:4px"></span></span>
      </a>
      <figcaption style="margin-top:.6em;font-size:.9em">Video: <b>${tittel}</b> (YouTube)<br>
        <a href="${lenke}">${lenke}</a></figcaption>`;
    f.replaceWith(fig);
    ut.push(lenke);
  });
  return ut;
}
"""

# Krymp figurar som er høgare enn grensa; bilete beheld forholdet mellom breidd og høgd.
JS_FIGUR = r"""
(maks) => {
  const ut = [];
  document.querySelectorAll('main img, main iframe, main video, main .leaflet-container').forEach(e => {
    const r = e.getBoundingClientRect();
    if (r.height <= maks) return;
    if (e.tagName === 'IMG') {
      e.style.setProperty('height', maks + 'px', 'important');
      e.style.setProperty('width', (r.width * maks / r.height) + 'px', 'important');
      e.style.setProperty('max-width', '100%', 'important');
      e.style.setProperty('object-fit', 'contain', 'important');
      e.style.setProperty('margin-left', 'auto');
      e.style.setProperty('margin-right', 'auto');
    } else {
      e.style.setProperty('height', maks + 'px', 'important');
    }
    ut.push((e.alt || e.tagName) + ': ' + Math.round(r.height) + ' -> ' + Math.round(maks) + ' px');
  });
  return ut;
}
"""

# Forside: tittel over, logo i midten, tekst under. Skrift og fargar blir henta frå
# dei same tekstane i toppfeltet på framsida.
JS_FORSIDE = r"""
({src, over, under}) => {
  const finn = t => [...document.querySelectorAll('body *')]
      .filter(e => e.offsetParent && (e.innerText || '').replace(/\s+/g, ' ').trim().startsWith(t))
      .sort((a, b) => a.innerText.length - b.innerText.length)[0];
  const stil = e => { if (!e) return ''; const c = getComputedStyle(e);
      return `color:${c.color};font-family:${c.fontFamily.replace(/"/g, "'")};font-weight:${c.fontWeight};font-style:${c.fontStyle};`; };
  const s1 = stil(finn('Bylovsjubileet')), s2 = stil(finn('Magnus Lagab')), s3 = stil(finn('Digital utstilling'));
  const f3 = s3.match(/font-family:[^;]*;/) ? s3.match(/font-family:[^;]*;/)[0] : '';
  const st = document.createElement('style');
  st.textContent = 'html,body{margin:0!important;padding:0!important;background:#fff!important}' +
                   'body>*:not(#forside){display:none!important}';
  document.head.appendChild(st);
  document.body.insertAdjacentHTML('afterbegin', `
    <div id="forside" style="width:210mm;height:296mm;box-sizing:border-box;padding:20mm 18mm;
         display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center">
      <div style="${s1}font-size:34pt;line-height:1.15">${over[0]}</div>
      <div style="${s2}font-size:19pt;line-height:1.3;margin:3mm 0 12mm">${over[1]}</div>
      <img src="${src}" style="max-height:160mm;max-width:150mm;display:block">
      <div style="${s3}font-size:14pt;margin-top:12mm">${under[0]}</div>
      <div style="${f3}font-size:12pt;margin-top:2.5mm;color:#555">${under[1]}</div>
    </div>`);
  return [s1, s2, s3];
}
"""

rows = [r for r in csv.DictReader(open(SRC, encoding="utf-8-sig"), delimiter=";")
        if FRA <= int(r["rekkjefølgje"]) <= TIL]


def opne(ctx, url):
    pg = ctx.new_page()
    pg.goto(url, wait_until="load", timeout=120000)
    try:
        pg.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        pass  # t.d. video/kart som held fram med å laste
    return pg


logg = []
with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge")
    ctx = b.new_context(color_scheme="light", locale="nn-NO",
                        viewport={"width": round(BREI_PX / SKALA), "height": 1000})
    for r in rows:
        nr, url = int(r["rekkjefølgje"]), r["url"]
        post = {"nr": nr, "tittel": r["tittel"], "nivå": int(r["nivå"]), "url": url, "fil": None, "sider": 0}
        if not url:
            logg.append(post)
            continue
        try:
            pg = opne(ctx, url)
            framside = int(r["nivå"]) == 0
            heimoppsett = pg.evaluate("!!document.querySelector('#nd-home-layout')")
            pg.add_style_tag(content=CSS_FRAMSIDE if framside else (CSS_HEIMSIDE if heimoppsett else CSS_ARTIKKEL))
            post["oppsett"] = "framside" if framside else ("heim" if heimoppsett else "artikkel")
            pg.emulate_media(media="screen")
            videoar = pg.evaluate(JS_VIDEO)
            if videoar:
                post["videoar"] = videoar
            manglar = pg.evaluate(JS_BILETE)
            pg.wait_for_timeout(500)
            krympa = pg.evaluate(JS_FIGUR, MAKS_FIGUR_PX)
            pg.wait_for_timeout(300)
            if framside:
                # Framsida er første tekstside. Hovudbiletet («Full logo») blir i tillegg
                # brukt på forsida saman med tittel og undertekst.
                src = pg.evaluate("""() => { const i = document.querySelector('img[alt="Full logo"]')
                    || [...document.images].sort((a, b) => b.width * b.height - a.width * a.height)[0];
                    return i.currentSrc || i.src; }""")
                fp = opne(ctx, url)
                stilar = fp.evaluate(JS_FORSIDE, {"src": src, "over": FORSIDE_OVER, "under": FORSIDE_UNDER})
                fp.wait_for_function("() => { const i = document.querySelector('#forside img'); return i && i.complete; }")
                fp.emulate_media(media="screen")
                ff = os.path.join(OUT, "forside_bilete.pdf")
                fp.pdf(path=ff, format="A4", print_background=True, margin={k: "0mm" for k in MARG})
                fp.close()
                assert pymupdf.open(ff).page_count == 1, "forsida vart meir enn éi side"
                post.update({"forside_bilete": src, "forside_fil": ff, "forside_stilar": stilar})
            h1 = pg.evaluate("(document.querySelector('#nd-page h1') || {}).innerText || ''")
            fil = os.path.join(OUT, f"side_{nr:02d}.pdf")
            pg.pdf(path=fil, format="A4", print_background=True, scale=SKALA,
                   margin={k: f"{v}mm" for k, v in MARG.items()})
            pg.close()
            n = pymupdf.open(fil).page_count
            post.update({"fil": fil, "sider": n, "h1": h1, "manglande_bilete": manglar, "krympa": krympa})
            print(nr, r["tittel"], "| sider:", n, "| h1:", h1, "| manglar:", manglar, "| krympa:", krympa, flush=True)
        except Exception as e:
            post["feil"] = repr(e)
            print("FEIL", nr, r["tittel"], repr(e), flush=True)
            traceback.print_exc()
        logg.append(post)
    b.close()

# Slå saman med tidlegare køyringar, så ein kan teikne opp enkeltsider på nytt.
JSN = os.path.join(OUT, "_render.json")
alle = {x["nr"]: x for x in (json.load(open(JSN, encoding="utf-8")) if os.path.exists(JSN) else [])}
alle.update({x["nr"]: x for x in logg})
json.dump([alle[k] for k in sorted(alle)], open(JSN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
feil = [x for x in logg if x.get("feil")]
print("ferdig:", len(logg), "rader,", len(feil), "feil")
