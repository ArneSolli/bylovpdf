"""Skaler ned bilete i ein PDF til maks 150 ppi ut frå storleiken dei har på sida, og komprimer som JPEG.

Bruk: python pdf_krymp.py <inn.pdf> <ut.pdf>
"""
import os, sys
import pymupdf
# Stiar: skriptet ligg i <prosjekt>/skript/. Kjeldefiler og resultat ligg i <prosjekt>/,
# mellomdata (nedlasta tekst, historikk, PDF-mellomfiler) i <prosjekt>/mellomdata/.
SKRIPT = os.path.dirname(os.path.abspath(__file__))
PROSJEKT = os.path.dirname(SKRIPT)
SCR = os.path.join(PROSJEKT, "mellomdata")


INN, UT = sys.argv[1], sys.argv[2]
MAKS_PPI, KVALITET = 150, 80


def oversyn(doc):
    """(tal på biletplasseringar, høgaste effektive ppi, sum av biletdata i byte)"""
    n, maks, byte, sett = 0, 0.0, 0, set()
    for side in doc:
        for img in side.get_images(full=True):
            xref, w, h = img[0], img[2], img[3]
            for rect in side.get_image_rects(xref):
                if rect.width <= 0 or rect.height <= 0:
                    continue
                n += 1
                ppi = max(w / (rect.width / 72), h / (rect.height / 72))
                maks = max(maks, ppi)
            if xref not in sett:
                sett.add(xref)
                byte += len(doc.xref_stream_raw(xref) or b"")
    return n, maks, byte


doc = pymupdf.open(INN)
f = oversyn(doc)
print(f"før:   {os.path.getsize(INN) / 1e6:.1f} MB | {f[0]} bilete på sidene | høgaste ppi {f[1]:.0f} | biletdata {f[2] / 1e6:.1f} MB")
# NB: doc.rewrite_images() i MuPDF øydelegg mønsterressursar (Pattern) som Edge brukar
# for somme bilete (sjå Julevakt), så han blir ikkje brukt. I staden blir kvart bilete
# skalert til 150 ppi ut frå den største plasseringa det har i dokumentet, og berre
# biletdata blir bytte ut – sideinnhaldet blir ikkje rørt.
maal = {}
for side in doc:
    for img in side.get_images(full=True):
        xref = img[0]
        for r in side.get_image_rects(xref):
            if r.width <= 0 or r.height <= 0:
                continue
            tw, th = r.width / 72 * MAKS_PPI, r.height / 72 * MAKS_PPI
            a = maal.get(xref, (0, 0, side.number))
            maal[xref] = (max(a[0], tw), max(a[1], th), a[2])

def skriv(xref, data, w, h, cs, filt):
    """Byt ut straumen i biletobjektet xref og set nøklane som høyrer til."""
    if filt:  # ferdig komprimert (JPEG)
        doc.update_stream(xref, data, compress=False)
        doc.xref_set_key(xref, "Filter", filt)
    else:     # rå pikslar: la MuPDF komprimere med Flate
        doc.update_stream(xref, data, compress=True)
    for k in ("DecodeParms", "Decode"):
        doc.xref_set_key(xref, k, "null")
    doc.xref_set_key(xref, "Width", str(w))
    doc.xref_set_key(xref, "Height", str(h))
    doc.xref_set_key(xref, "ColorSpace", cs)
    doc.xref_set_key(xref, "BitsPerComponent", "8")


endra, jpeg_om = 0, 0
for xref, (tw, th, pno) in maal.items():
    base = pymupdf.Pixmap(doc, xref)
    nw, nh = min(base.width, round(tw)), min(base.height, round(th))
    skal_skalerast = nw < base.width or nh < base.height
    if not skal_skalerast:
        # Under 150 ppi frå før: komprimer på nytt som JPEG berre om biletet er lagra
        # utan tap (Flate) og er stort nok til at det monnar.
        filt = doc.xref_get_key(xref, "Filter")[1]
        raa = len(doc.xref_stream_raw(xref) or b"")
        if "FlateDecode" not in filt or raa < 100_000 or base.width < 64 or base.height < 64:
            continue
    if base.colorspace and base.colorspace.n not in (1, 3):
        base = pymupdf.Pixmap(pymupdf.csRGB, base)
    if base.alpha:
        base = pymupdf.Pixmap(base, 0)  # fjern eventuell alfakanal; masken (SMask) står for seg
    liten = pymupdf.Pixmap(base, nw, nh, None) if skal_skalerast else base
    data = liten.tobytes("jpeg", jpg_quality=KVALITET)
    if not skal_skalerast and len(data) > 0.8 * raa:
        continue  # JPEG sparer for lite
    # Skriv dei nye biletdata rett inn i det eksisterande biletobjektet (ingen nye objekt).
    skriv(xref, data, nw, nh, "/DeviceGray" if liten.n == 1 else "/DeviceRGB", "/DCTDecode")
    smask = doc.xref_get_key(xref, "SMask")
    if skal_skalerast and smask[0] == "xref":
        # Masken (gjennomsikt) blir skalert til same storleik og lagra som Flate.
        mx = int(smask[1].split()[0])
        maske = pymupdf.Pixmap(pymupdf.Pixmap(doc, mx), nw, nh, None)
        skriv(mx, maske.samples, nw, nh, "/DeviceGray", None)
    if skal_skalerast:
        endra += 1
    else:
        jpeg_om += 1
print("skalerte", endra, "bilete til", MAKS_PPI, "ppi | komprimerte", jpeg_om, "bilete under grensa på nytt som JPEG")

# Bilete som ikkje er plasserte direkte på ei side (t.d. inne i mønster) blir ikkje rørte; rapporter dei store.
urort = [(x, len(doc.xref_stream_raw(x) or b"")) for x in range(1, doc.xref_length())
         if doc.xref_get_key(x, "Subtype")[1] == "/Image" and x not in maal]
store = [u for u in urort if u[1] > 200_000]
print("bilete utan direkte plassering:", len(urort), "| av dei over 200 kB:", [(x, f"{b / 1e6:.1f} MB") for x, b in store])

doc.save(UT, garbage=4, deflate=True)
doc.close()
d2 = pymupdf.open(UT)
e = oversyn(d2)
print(f"etter: {os.path.getsize(UT) / 1e6:.1f} MB | {e[0]} bilete på sidene | høgaste ppi {e[1]:.0f} | biletdata {e[2] / 1e6:.1f} MB")
interne = sum(1 for s in d2 for l in s.get_links() if l["kind"] == pymupdf.LINK_GOTO)
print("sider:", d2.page_count, "| bokmerke:", len(d2.get_toc()), "| interne lenker (innhaldslista):", interne)
