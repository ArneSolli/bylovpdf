# bylovpdf – PDF-utskrift av nettutstillinga *Bylovsjubileet 1276–2026*

Python scripts that turn the University of Bergen web exhibition *Bylovsjubileet 1276–2026* into a single printable PDF.

Skripta i dette repoet overfører nettutstillinga [Bylovsjubileet 1276–2026](https://bylovsjubileet.uib.no/) til éin PDF. Den fungerer som utskrift og som samla kopi av innhaldet. Kjeldekoden til sjølve utstillinga ligg i [uib-ub/exhibition-bylov750-nextra](https://github.com/uib-ub/exhibition-bylov750-nextra).

PDF-en blir bygd opp slik:

| Side | Innhald |
|---|---|
| 1 | Forside med logo og tittel |
| 2 | Blank |
| 3 | Forord (`skript/Forord.md`) |
| 4 | Innhaldsliste, klikkbar |
| 5 ff. | Alle sidene i utstillinga i menyrekkjefølgje, utan menyar, søkjefelt og botnfelt |
| Siste | Bakside. Talet på sider er alltid partal, med ei blank side framfor baksida ved behov. |

Andre eigenskapar:
- PDF-en har sidetal og bokmerke.
- Bileta er skalerte til maks 150 ppi.
- Ingen figurar er høgare enn to tredjedelar av sida.
- Videoar er viste med eit stillbilete og ei lenke.

## Innhald

| Fil / mappe | Kva |
|---|---|
| `skript/hent_artikkelliste.py` | Crawlar som finn alle sidene i utstillinga (tittel, forfattar, URL). Han samanliknar òg med ordna-fila. |
| `ordna/bylovsjubileet_artiklar_ordna.csv` | Rekkjefølgje og nivå for alle sidene. Fila blir halden ved like for hand. Rader utan URL er mellomtitlar. |
| `bylovsjubileet_artiklar.csv` | Den opphavlege sidelista (frå første crawling 2026-11-25) |
| `skript/pdf_render.py` | Opnar kvar side i Microsoft Edge og skriv ut hovudinnhaldet som PDF |
| `skript/pdf_set_saman.py` | Set saman forside, forord, innhaldsliste, sidene og bakside, og legg til sidetal og bokmerke. Teksten på baksida står i `BAKSIDE` øvst i skriptet. |
| `skript/pdf_krymp.py` | Skalerer ned bileta til maks 150 ppi |
| `skript/Forord.md` | Forordet. Rediger det før ny generering. |
| `skript/bylov_ordne.py` | Laga første utgåve av ordna-fila. Det skriv ikkje over henne utan `--overskriv`. |
| `CLAUDE.md` | Detaljerte arbeidsnotat: krav, kjende fallgruver og korleis nettstaden er bygd |

CSV-filene er semikolonseparerte og i UTF-8 med BOM, slik at Excel opnar dei rett.

## Krav

- Python 3.12 eller nyare.
- Pakkane `requests`, `beautifulsoup4`, `playwright`, `pymupdf` og `markdown`:
  ```
  python -m pip install requests beautifulsoup4 playwright pymupdf markdown
  ```
- Microsoft Edge. Skripta brukar Edge gjennom Playwright (`channel="msedge"`), så nettlesaren til Playwright treng ikkje installerast.

## Køyring

Køyr frå rotmappa i repoet:

1. **Sjekk sidelista** (valfritt):
   ```
   python skript/hent_artikkelliste.py
   ```
   Skriptet seier ifrå om nye sider, sider som manglar, eller titlar som har endra seg. Nye sider må leggjast inn i `ordna/bylovsjubileet_artiklar_ordna.csv` for hand.
2. **Skriv ut sidene.** Dette tek om lag 10 minutt. Det siste talet er den siste rekkjefølgja i ordna-fila.
   ```
   python skript/pdf_render.py 0 44
   ```
3. **Set saman:**
   ```
   python skript/pdf_set_saman.py mellomdata/pdf_test/heile_fullopploysing.pdf
   ```
4. **Krymp bileta:**
   ```
   python skript/pdf_krymp.py mellomdata/pdf_test/heile_fullopploysing.pdf pdf/bylovsjubileet_heile_utstillinga.pdf
   ```

Har du berre endra forordet, er det nok å køyre steg 3 og 4.

## Det som ikkje er med

Mappene `pdf/` og `mellomdata/` er utelatne med vilje. Den ferdige PDF-en og mellomfilene inneheld tekstar og bilete frå utstillinga, og opphavsretten til dei ligg hos forfattarane og fotografane.

## Opphav og lisens

Skripta er utvikla av Arne Solli med bruk av Claude (Opus 5.5), 26. november 2026. Crawlaren byggjer på eit tidlegare skript av Arne Solli.

Skripta er lisensierte under [MIT-lisensen](LICENSE). Lisensen gjeld koden i dette repoet. Han gjeld ikkje tekstane og bileta i utstillinga, for dei høyrer til forfattarane og rettshavarane.
