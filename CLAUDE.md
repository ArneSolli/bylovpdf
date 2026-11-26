# CLAUDE.md – Bylovsjubileet: PDF-utskrift av nettutstillinga

Felles reglar (språk, filformat, kjeldebruk, personvern, Python) står i `claude\CLAUDE.md`. Denne fila gjeld berre dette prosjektet.

## Føremål
Lage ei utskrift av heile nettutstillinga *Bylovsjubileet 1276–2026* (https://bylovsjubileet.uib.no/) som éin PDF.

## Arbeidsflyt
1. **`skript/hent_artikkelliste.py`** er ein crawlar som startar på framsida og finn alle sidene i utstillinga, med tittel, forfattar og URL. Resultatet går til `mellomdata/artikkelliste_crawl.csv`. Skriptet viser òg kva som skil lista frå ordna-fila: nye sider, sider som manglar, og ulike titlar.
   - **Opphav:** Skriptet byggjer på brukaren sitt eige skript, `bylovjub.py`, som laga `bylovsjubileet_artiklar.csv` 2026-11-25. Originalskriptet er ikkje lenger i prosjektet. Ei ny køyring av det 2026-11-26 gav ei fil som var identisk byte for byte.
   - **Kvifor ein ny versjon:** Originalen las berre `<a href>`-lenker. Sidene under `/kreditering/` finst berre i navigasjonsdataa som Next.js legg inn i sida som JSON, og menyen blir laga med JavaScript. Difor måtte dei leggjast inn for hand.
   - **Endringar frå originalen:**
     - Han les òg navigasjonsdataa.
     - Han slår saman `/no/…` med `/…`, slik at det ikkje blir duplikat.
     - Han tek ikkje med knappeteksten «Copy Anchor Link» i overskrifta.
     - Han skriv til `mellomdata/` og ikkje over originalfila.
2. **`skript/bylov_ordne.py`** laga første utgåve av `ordna/bylovsjubileet_artiklar_ordna.csv` med rekkjefølgje og nivå frå menylista til brukaren.
3. **Manuelt steg:** Ordna-fila blir halden ved like for hand. Nye sider frå steg 1 må leggjast inn med rekkjefølgje og nivå. Kreditteringsradene vart lagde inn slik.
4. **PDF-skripta** les ordna-fila. Sjå «Køyring» nedanfor.

**Status 2026-11-26:** Crawlaren finn 37 sider, og alle er i ordna-fila. To av dei står ikkje i menyane på nettstaden, men vart lagde inn etter avtale med brukaren:
- **«Frå bylov til kommunelov»** (`/c/etterliv/kommunelov`, av Arne Solli, rad 39). Sidetreet på nettstaden gjev ingen plass for han, for han er hengd på til slutt. Han står etter formannskapslova av di han handlar om det same emnet.
- **«Bilete»** (`/kreditering/bilete`, rad 44). Ho står sist under Kreditering, slik som i sidetreet.

## Kjelder
- `bylovsjubileet_artiklar.csv` er originalfila frå brukaren sitt skript `bylovjub.py`. Ho skal ikkje endrast. Fila har 37 rader og kolonnane tittel, forfatter og url. Rad 34–37 er duplikat under `/no/c/` av rad 1, 12, 16 og 21.
- `ordna/bylovsjubileet_artiklar_ordna.csv` styrer rekkjefølgja og nivåa, og **blir halden ved like for hand av brukaren**. Det er denne fila PDF-skripta les. Kolonnane er rekkjefølgje, nivå, tittel, forfatter og url. Status 2026-11-26: 45 rader, 0–44.
  - **Nivå 0:** framsida.
  - **Nivå 1–3:** talet på ledd i stien etter `/c/`.
  - **Rader utan URL:** overskrifter (mellomtitlar). Stiane deira gjev 404.
  - **Kreditering:** rad 41–44 ligg under `/kreditering/` og ikkje under `/c/`.
  - **Tittel:** same som overskrifta (h1) på sida.
  - I `mellomdata/` ligg to kopiar frå 2026-11-26:
    - Fila slik brukaren lagra henne, før kolonnane i to av kreditteringsradene vart retta.
    - Fila før «Frå bylov til kommunelov» og «Bilete» vart lagde inn.

## Nettstaden
- Nettstaden er bygd med Next.js og Fumadocs og ligg på Vercel. Han har ingen datometadata, ingen `sitemap.xml` og ingen kopiar i Wayback Machine.
- På artikkelsidene er `#nd-sidebar` venstremenyen og `#nd-subnav` toppramma, medan `#nd-page` er artikkelen.
- Den klebrige menyen «på denne sida» er `[data-toc-popover]`.
- Framsida og `/kreditering/*` brukar `#nd-home-layout`, med `#nd-nav` som menylinje øvst og `footer` nedst.
- Hovudbiletet på framsida er `img[alt="Full logo"]` (`UiB_Bylovjubileet_2026_Initial.svg`). Fargane i SVG-fila ligg i CSS-klassar, og MuPDF teiknar henne difor i svart. Bruk Edge.

## Krav til PDF-en (`pdf/bylovsjubileet_heile_utstillinga.pdf`)
Krava er avtalte med brukaren:
- **Side 1:** forside med «Bylovsjubileet 1276–2026» og «Magnus Lagabøtes Bylov i 750 år» over logoen. Under logoen står «Digital utstilling ved Universitetet i Bergen» og https://bylovsjubileet.uib.no/.
- **Side 2:** blank.
- **Side 3:** forordet frå `skript/Forord.md`.
- **Side 4:** innhaldslista på **éi** side. Overskrifter utan URL er utheva og har ikkje sidetal.
- **Side 5:** heile framsida er første tekstside. Kvar post byrjar på ny side.
- Blir forordet lengre enn éi side, flyttar innhaldslista og teksten seg bakover tilsvarande.
- **Siste side:** baksida med «Bylovsjubileet 1276–2026», «Universitetet i Bergen» og «2026». Ho har same skrift og fargar som forsida, henta frå `forside_stilar` i `_render.json`.
  - Teksten står i `skript/Bakside.md`, som brukaren og prosjektleiaren redigerer. Kvar linje blir éi tekstlinje, og tomme linjer og kommentarar (`<!-- -->`) blir hoppa over. Manglar fila, brukar skriptet standardteksten i `BAKSIDE_STANDARD`.
  - Talet på sider skal vere partal, slik at baksida ligg på baksida av eit ark. Ved behov blir det sett inn ei blank side framfor henne.
  - Baksida og den blanke sida har ikkje sidetal.
- **Kva som er teke bort:** venstremenyen, toppramma, botnfeltet med kreditering og navigasjonen for førre og neste side.
- **Figurar:** maks 66 % av A4-høgda (196 mm). Forsida er unnateken.
- **Bilete:** maks 150 ppi ut frå storleiken dei har på sida, lagra som JPEG med kvalitet 80.
- **Video:** YouTube-ramer blir erstatta med førehandsbiletet og ei klikkbar lenke.
- **Navigasjon:** sidetal frå første tekstside, bokmerke (Forside, Forord, Innhald, alle postar og Bakside) og klikkbar innhaldsliste.
- **Kjeldemerknad:** Merknaden under innhaldslista har datoen sidene vart henta. Datoen blir teken frå når `pdf_render.py` sist køyrde.

## Forord (`skript/Forord.md`)
Forordet er ei Markdown-fil som brukaren og prosjektleiaren redigerer før dei lagar PDF-en på nytt. Det fortel kort korleis skripta overfører nettsidene til PDF, og kven som har laga skripta: Arne Solli med Claude (Opus 5.5), 26. november 2026.
- `pdf_set_saman.py` gjer Markdown om til HTML og teiknar det opp med same skrift som nettstaden.
- Viss fila manglar, blir det ikkje noko forord.
- Fila ligg i `skript/`, så ho kjem med på GitHub.

## Køyring
Bruk Python-tolken frå den globale CLAUDE.md. Køyr frå prosjektmappa:
1. `skript/pdf_render.py 0 44` teiknar opp sidene i Edge til `mellomdata/pdf_test/`. Det siste talet er den siste rekkjefølgja i ordna-fila. Dette tek om lag 10 minutt.
2. `skript/pdf_set_saman.py mellomdata/pdf_test/heile_fullopploysing.pdf` lagar forside, blank side, forord og innhaldsliste og set alt saman. Har du berre endra forordet, er det nok å køyre steg 2 og 3, så lenge `mellomdata/pdf_test/` finst.
3. `skript/pdf_krymp.py mellomdata/pdf_test/heile_fullopploysing.pdf pdf/bylovsjubileet_heile_utstillinga.pdf` skalerer ned bileta. Fila går frå om lag 130 MB til 7 MB.

Det som trengst:
- Pakkane `playwright`, `pymupdf` og `markdown`.
- Microsoft Edge (`channel="msedge"`). Nettlesaren til Playwright trengst ikkje.

`pdf_render.py` kan teikne opp utvalde rader på nytt, til dømes med `35 35`. Resultatet blir slått saman med `_render.json`.

`bylov_ordne.py` laga første utgåve av ordna-fila. Det skriv ikkje over henne utan `--overskriv`.

## Kjende fallgruver
- `pymupdf.Document.rewrite_images()` øydelegg mønsterressursane (Pattern) som Edge lagar, og skal **ikkje** brukast. `pdf_krymp.py` byter berre ut biletdata.
- Innhaldslista skal få plass på éi side. Skriptet krympar henne først til 62 %, går så over til tettare linjeavstand og krympar vidare ned til 52 %. Kjem det mange fleire rader, må oppsettet endrast, til dømes med to spalter.
- `:has()` kan ikkje stå inne i ein annan `:has()` i CSS. Då blir heile regelen ignorert.
- Biletrader med `md:flex-row > [class*="lg:w-"]` blir tvinga til lik breidd. Elles blir det andre biletet berre 72 px breitt.

## Mapper
| Mappe | Innhald |
|---|---|
| `ordna/` | Rekkjefølgje og nivå, halden ved like for hand |
| `pdf/` | Ferdig PDF |
| `skript/` | `hent_artikkelliste.py`, `bylov_ordne.py`, `pdf_render.py`, `pdf_set_saman.py`, `pdf_krymp.py`, `Forord.md` og `Bakside.md` |
| `mellomdata/` | Resultatet av crawlinga (`artikkelliste_crawl.csv`), kopien av ordna-fila og `pdf_test/`, som er mellomfiler frå PDF-køyringa og blir laga på nytt |

## Git og GitHub
Prosjektmappa er eit git-repo med greina `main`. Commitane står på Arne Solli `<arne.solli@uib.no>`. Namn og e-post er sette berre for dette repoet.
- **Med i repoet:** `README.md`, `LICENSE`, `CLAUDE.md`, `bylovsjubileet_artiklar.csv`, `ordna/` og `skript/` med `Forord.md` og `Bakside.md`.
- **Lisens:** Skripta har MIT-lisens. Lisensen gjeld ikkje tekstane og bileta i utstillinga.
- **GitHub:** Repoet ligg offentleg på https://github.com/ArneSolli/bylovpdf, og `main` følgjer `origin/main`. Innlogginga er lagra i Git Credential Manager. Alle dei offentlege repoa i `uib-ub` er òg opne, men 24 av 35 manglar lisens (2026-11-26).
- **Utelate:** `.gitignore` er ei kviteliste og held ute `pdf/` og `mellomdata/`. Dei har opphavsrettsleg innhald frå utstillinga og filer som kan lagast på nytt.
- **Sjekka 2026-11-26:** Skripta inneheld ingen absolutte stiar, brukarnamn, e-postadresser eller nøklar. CSV-filene inneheld namna på forfattarane slik dei står på den offentlege nettstaden.
- **Plan:** Repoet skal seinare overførast til organisasjonen til Universitetsbiblioteket, [uib-ub](https://github.com/uib-ub), med *Settings → Transfer ownership*.
- **Kjeldekoden til utstillinga** ligg i `uib-ub/exhibition-bylov750-nextra`. Han kan gje menystrukturen direkte, om crawlinga ein gong ikkje er nok.

Prosjektet låg tidlegare i `prosjekt\sikt\bylovsjubileet` og vart flytta ut 2026-11-26. `sikt` er eit privat prosjekt og har ingenting med dette repoet å gjere.
