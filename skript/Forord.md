# Forord

Denne PDF-en er ei utskrift av nettutstillinga *Bylovsjubileet 1276–2026* (https://bylovsjubileet.uib.no/). Føremålet er å gjere utstillinga tilgjengeleg på papir og som ein samla kopi av innhaldet slik det låg på nettet då utskrifta vart laga.

Utskrifta er laga automatisk med eigne Python-skript. Dei overfører nettsidene til PDF i fire steg:

1. **Sidelista.** Skripta går gjennom nettstaden og finn alle sidene i utstillinga, med tittel, forfattar og adresse. Rekkjefølgja og inndelinga følgjer menyen i utstillinga.
2. **Utskrift av sidene.** Kvar side blir opna i ein nettlesar og skriven ut. Menyar, søkjefelt og andre delar som berre høyrer til nettsida, blir tekne bort, så berre sjølve innhaldet står att. Videoar blir viste med eit stillbilete og ei lenke.
3. **Samanstilling.** Sidene blir sette saman til éin PDF med forside, forord og innhaldsliste. PDF-en har sidetal, og innhaldslista og bokmerka er klikkbare.
4. **Tilpassing til A4.** Bilete blir skalerte ned til ei oppløysing som passar for trykk (maks 150 ppi). Ingen figurar tek meir enn to tredjedelar av sidehøgda.

Opphavsretten til tekstar og bilete ligg hos forfattarane og hos dei som er oppgitt ved kvart bilete.

Skripta er utvikla av Arne Solli med bruk av Claude (Opus 5.5), 26. november 2026.
