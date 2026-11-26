"""Laga første versjon av ordna/bylovsjubileet_artiklar_ordna.csv (rekkjefølgje og nivå frå menylista).

NB: Ordna-fila blir no halden ved like for hand (t.d. rad 40–42 om kreditering). Skriptet skriv
difor ikkje over ei eksisterande fil utan argumentet --overskriv.
"""
import csv, os, re, sys
# Stiar: skriptet ligg i <prosjekt>/skript/. Kjeldefiler og resultat ligg i <prosjekt>/,
# mellomdata (nedlasta tekst, historikk, PDF-mellomfiler) i <prosjekt>/mellomdata/.
SKRIPT = os.path.dirname(os.path.abspath(__file__))
PROSJEKT = os.path.dirname(SKRIPT)
SCR = os.path.join(PROSJEKT, "mellomdata")


SRC = os.path.join(PROSJEKT, "bylovsjubileet_artiklar.csv")
OUTDIR = os.path.join(PROSJEKT, "ordna")
OUT = os.path.join(OUTDIR, "bylovsjubileet_artiklar_ordna.csv")

LISTE = """
[Frå Landslov til Bylov](https://bylovsjubileet.uib.no/c/fraa-landslov-til-bylov)
[Omskriving av bolkar](https://bylovsjubileet.uib.no/c/fraa-landslov-til-bylov/omskriving)
[Kongens plass](https://bylovsjubileet.uib.no/c/fraa-landslov-til-bylov/kongens-plass)
[Byordninga](https://bylovsjubileet.uib.no/c/fraa-landslov-til-bylov/byskiping)
[Europeiske parallellar](https://bylovsjubileet.uib.no/c/fraa-landslov-til-bylov/europeiske-parallellar)
[Bylova og Skriftkultur](https://bylovsjubileet.uib.no/c/skriftkultur)
Bergens bylov i kontekst
[Andre bylover i Noreg](https://bylovsjubileet.uib.no/c/skriftkultur/i-kontekst/norge)
[Liknande lover i utlandet](https://bylovsjubileet.uib.no/c/skriftkultur/i-kontekst/utlandet)
[Rettarbøter](https://bylovsjubileet.uib.no/c/skriftkultur/i-kontekst/retterboeter)
[Diplom og Privilegium](https://bylovsjubileet.uib.no/c/skriftkultur/i-kontekst/diplom-og-privilegium)
Andre tekster
[Bjarkøyretten](https://bylovsjubileet.uib.no/c/skriftkultur/andre-tekster/bjarkoeyretten)
[Farmannslova](https://bylovsjubileet.uib.no/c/skriftkultur/andre-tekster/farmannslova)
[Hirdskrå](https://bylovsjubileet.uib.no/c/skriftkultur/andre-tekster/hirdskraa)
[Kongespegelen](https://bylovsjubileet.uib.no/c/skriftkultur/andre-tekster/kongespeilet)
Skrift og språk
[Skrivarar og illuminatørar](https://bylovsjubileet.uib.no/c/skriftkultur/skrift-og-spraak/skrivarar)
[Bylovas språk i diakroni](https://bylovsjubileet.uib.no/c/skriftkultur/skrift-og-spraak/diakroni)
[Danske omsetjingar](https://bylovsjubileet.uib.no/c/skriftkultur/skrift-og-spraak/danske-omsetjingar)
[Nedertysk omsetjing](https://bylovsjubileet.uib.no/c/skriftkultur/skrift-og-spraak/nedertysk-omsetjing)
[Bergens Bylov](https://bylovsjubileet.uib.no/c/bergens-bylov)
Bylov og byen
[Brann og ombygging](https://bylovsjubileet.uib.no/c/bergens-bylov/bylov-og-byen/brann-og-ombygging)
[Offentlege bygg](https://bylovsjubileet.uib.no/c/bergens-bylov/bylov-og-byen/offentlege-bygg)
[Handelsby Bergen](https://bylovsjubileet.uib.no/c/bergens-bylov/bylov-og-byen/handelsby)
Bylov og bergensarane
[Myndigheiter](https://bylovsjubileet.uib.no/c/bergens-bylov/bylov-og-bergensarane/myndigheiter)
[Hanseatane](https://bylovsjubileet.uib.no/c/bergens-bylov/bylov-og-bergensarane/hanseatane)
[Den religiøse byen](https://bylovsjubileet.uib.no/c/bergens-bylov/bylov-og-bergensarane/religionsby)
Årshjul
[Året i byen](https://bylovsjubileet.uib.no/c/bergens-bylov/aarshjul/aaret)
[Jula i byen](https://bylovsjubileet.uib.no/c/bergens-bylov/aarshjul/julefred)
[Julevakt](https://bylovsjubileet.uib.no/c/bergens-bylov/aarshjul/julevakt)
[Bylova og vektarane](https://bylovsjubileet.uib.no/c/bergens-bylov/video)
[Bylovas Etterliv](https://bylovsjubileet.uib.no/c/etterliv)
[Bylovas utvikling](https://bylovsjubileet.uib.no/c/etterliv/utvikling)
[Formannskapslov](https://bylovsjubileet.uib.no/c/etterliv/formannskapslov)
[Filologi og historiografi](https://bylovsjubileet.uib.no/c/etterliv/filologi-og-historiografi)
"""

# Les lista linje for linje: lenkjelinjer blir rader frå CSV-en, linjer utan lenke
# er mellomtitlar (nivå 2). Mellomledda gav 404 (sjekka 2026-11-26), så URL er tom.
post = []
for linje in LISTE.strip().splitlines():
    m = re.fullmatch(r"\[(.+?)\]\((https?://[^)]+)\)", linje.strip())
    post.append(("lenkje", m.group(2).rstrip("/")) if m else ("mellomtittel", linje.strip()))

pos = [v for t, v in post if t == "lenkje"]
assert len(pos) == len(set(pos)) == 33

rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig"), delimiter=";"))
felt_inn = list(rows[0].keys())
etter_url = {r["url"].strip().rstrip("/"): r for r in rows}
assert len(etter_url) == len(rows)
manglar = [u for u in pos if u not in etter_url]
assert not manglar, manglar
utanfor = [r for u, r in etter_url.items() if u not in pos]
assert all("/no/c/" in r["url"] and r["url"].replace("/no/c/", "/c/", 1).rstrip("/") in pos for r in utanfor), utanfor


def segment(url):
    sti = url.strip().rstrip("/").split("bylovsjubileet.uib.no", 1)[1]
    seg = [s for s in sti.split("/") if s]
    assert seg[0] == "c", url
    return seg[1:]


ut = [{"rekkjefølgje": 0, "nivå": 0, "tittel": "Bylovsjubileet 1276–2026",
       "forfatter": "", "url": "https://bylovsjubileet.uib.no/"}]
for k, (t, v) in enumerate(post):
    if t == "lenkje":
        r = dict(etter_url[v])
        r["nivå"] = len(segment(v))
    else:
        # Kontroller at lenkjene under mellomtittelen deler same mellomledd i stien.
        under = []
        for t2, v2 in post[k + 1:]:
            if t2 != "lenkje" or len(segment(v2)) != 3:
                break
            under.append(segment(v2)[:2])
        assert under and all(s == under[0] for s in under), (v, under)
        r = {"tittel": v, "forfatter": "", "url": "", "nivå": 2, "_sti": "/".join(under[0])}
    r["rekkjefølgje"] = len(ut)
    ut.append(r)

# Alle nivå-3-rader skal liggje rett under ein mellomtittel med same mellomledd.
gjeld = None
for r in ut:
    if r["nivå"] == 2 and not r["url"]:
        gjeld = r["_sti"]
    elif r["nivå"] == 3:
        assert "/".join(segment(r["url"])[:2]) == gjeld, r
    elif r["nivå"] < 2:
        gjeld = None

if os.path.exists(OUT) and "--overskriv" not in sys.argv:
    raise SystemExit(f"{OUT} finst og blir halden ved like for hand. Bruk --overskriv for å lage ho på nytt.")
os.makedirs(OUTDIR, exist_ok=True)
with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["rekkjefølgje", "nivå"] + felt_inn, delimiter=";", extrasaction="ignore")
    w.writeheader()
    w.writerows(ut)

from collections import Counter
print("rader:", len(ut), "| nivå:", sorted(Counter(r["nivå"] for r in ut).items()))
print("sletta duplikat:", [r["url"] for r in utanfor])
for r in ut:
    if r["nivå"] == 2 and not r["url"]:
        print("mellomtittel:", r["rekkjefølgje"], r["tittel"], "->", r["_sti"])
