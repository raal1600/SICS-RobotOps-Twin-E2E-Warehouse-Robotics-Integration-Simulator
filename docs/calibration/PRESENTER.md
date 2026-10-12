# Visa den uppmätta robotcellen

Den lokala syntetiska demonstrationen har klarat SC01-SC20 enligt
ACCEPTANCE_REPORT.md. Bilder och mätvärden beräknas på nytt; inga industrirobotar
ansluts. Begränsningar och återstående verklig driftsättning beskrivs i LIMITATIONS.md.

## Starta och kalibrera

Starta enligt projektets lokala instruktioner, exempelvis från repots rot:

```powershell
uv run --locked python -m apps.api --runtime headless --data-dir runs/calibration-presenter-new --port 8093
```

Välj en ny datamapp och ledig port. Öppna `http://127.0.0.1:8093`.

1. Välj **Start new test**, **Measured calibration cell** och ett frö, exempelvis 37.
   **Controller command reference** väljer fläns eller TCP för den nya cellen.
   Säg: ”I flänsläget räknar Python bort verktygsoffseten. I TCP-läget använder
   styrenheten sitt konfigurerade verktyg. Offseten får bara användas en gång.”
2. För första kameran: **Configure camera → Acquire board images → Estimate calibration**.
   Öppna **Acquired sensor images**. Det är sparade RGB-bilder, djupdata och faktiskt
   detekterade hörn. Kandidaten är fortfarande inaktiv.
3. Välj **Validate independently**. Öppna **Inspect calibration evidence** och välj
   valideringsrapporten. Visa separat PnP-fel, robotkedjans bildfel och oberoende
   referensfel. Gå tillbaka via **Run & watch**.
4. Ange ett namn och välj **Approve for this simulation**. Upprepa för den andra kameran.
5. Välj **Remove board and check tool**. Kontrollen sparar pivotlägen och separata
   mätpunkter som kontrollerar verktygets riktning. Kamerans godkännande ersätter inte
   verktygskontrollen.

Förklara: ”Avståndet säger var punkten ligger i kamerans system. Vi behöver också
beräkna var kameran sitter i förhållande till roboten. Fabrikens optiska kalibrering
bestämmer inte den installationen. Bilder från olika lägen och vinklar ger information
som många nästan likadana bilder saknar. Vi skattar geometriska parametrar; vi tränar
inte ett beteende genom belöningar.”

## Kör och följ bevisen

### Visa varför mätningarnas kvalitet spelar roll

Efter **Configure camera**, öppna **Measurement plan and quality experiments**.
Välj exempelvis **Repeat one pose** och ta bilderna. **Improve measurements** visar
att många accepterade bilder ändå saknar läges- och rotationsvariation. Under
**Inspect calibration evidence**, välj posten `acquisition-report`: antal bilder,
förkastade mätningar och täckning beräknas i Python.

**Rotate about one axis only** visar att varierade positioner inte ersätter olika
rotationsaxlar. **Depth timestamps 100 ms late** och **Capture before settling**
sparar bilderna med tydliga avvisningsskäl. Gå vidare med **Improve measurements**,
välj **Varied, settled measurements** och ta en ny mätserie. Inga tidigare fel
raderas och inget godkännande skapas av att bilder tas.

För att visa optikens separata roll, använd **Wrong configured focal length** eller
ett profilfel i felpanelen och välj **Record changed camera model**. Kontrollens
egna syntetiska fabriksreferenser avvisar den felaktiga modellen. De mäter inte var
kameran sitter i robotcellen. Återställ modellen och kontrollera den innan en ny
installationskalibrering görs.

### Följ ett faktiskt plock

1. Välj **Run a guided pick**. Följ konsolens tillåtna steg och ge separat uttryckligt
   tillstånd när robotkörningen begärs.
2. Efter avslut: välj **Inspect evidence**. Följ runtime-point, runtime-target och
   kommandot. Visa pixel, rått djup, skala, stråle, T_c_d, X, baspunkt och TCP/flänsmål.
3. I bildpanelen: öppna **Inspect an RGB pixel and its depth**. Ange kolumn/rad eller
   välj i RGB-bilden. **Inspect pixel** gör en läsande Python-beräkning på sparade data.
   Registrerat djup kan ha hål; inga värden fylls i för att få ett bekvämt svar.
4. Visa **Saved excerpt** och **Full Python file**. Sparad beräkning och dagens
   referenskod har olika betydelse. Komponentlistan är en kodkatalog, inte en animation
   som påstår att varje rad kördes.

Förklara: ”En uppmätt punkt är inte ett färdigt grepp. Riktning, kontaktpunkt,
angreppsväg och verktygsgeometri kommer från separata angivna förutsättningar.
Den här förenklade igenkänningen använder kända färgmarkerade klossar, inte alla varor.”

## Flytta kameran och återhämta

1. Öppna **Checks and controlled recovery → Introduce a simulated camera fault**.
   Välj **Move camera in this simulation**. Den fysiska kameran flyttas; X ändras inte.
2. Visa blockeringen och välj **Measure routine references**. Inspektera felvektorer
   och resultat. Den gamla versionen finns kvar för granskning men får inte användas.
3. Välj **Start new measurements → Acquire board images → Estimate calibration →
   Validate independently**. Ge nytt uttryckligt godkännande.
4. Kontrollera verktyget när gränssnittet begär det. Fyll på via den befintliga
   testhanteringen om föregående kloss redan har levererats. Kör ett nytt guidat plock.

Förklara: ”Ett missat plock bevisar inte att kamerans transform är fel. Vi kontrollerar
referenser, montering, djup, tidsstämplar och verktyg var för sig. Om mätningarna inte
skiljer orsakerna åt måste svaret vara otillräckligt underlag.”

## Visa skillnaden mellan djupfel och verktygsfel

Under **Sensor and tool fault experiments**:

- Välj **Tool tip moved 15 mm**, applicera och välj **Measure and verify the tool**.
  Visa det underkända verktygsresultatet och dess råa pivot/probmätningar. Kamerans X
  är oförändrat. **Restore the indexed tool** kräver sedan en ny verktygskontroll.
- Välj **Depth scale +8%**, applicera och mät rutinkontrollens referenser. Den visar
  ett skalningsliknande felmönster, inte en garanterad diagnos. Ändra inte X för att
  dölja skalfelet.
- Välj **Missing depth: non-finite returns**, mät referenser och inspektera en sparad
  bild/pixel. Visa `NO_VALID_DEPTH`: ingen nollpunkt eller reservposition skapas.
- **Restore nominal sensor output** återställer bara sensorn. En godkänd rutinkontroll
  återaktiverar inte en misstänkt kalibrering; följ nya mätningar, validering och godkännande.

Numeriska toleranser är märkta **SIMULATION_ONLY** och bygger på denna kloss,
kontaktgeometri och brusmodell. Rapporten anger inga verifierade SICS-produktionstoleranser.

## Byt tavlans montering utan att påstå att kameran flyttades

I **Sensor, board and tool experiments**, välj **Remount the calibration board**.
Båda kamerorna ska bli blockerade eftersom de delar samma tavla och monterings-ID.
De sparade X-värdena ändras inte av knappen. Välj **Record changed board** för varje
kamera och följ nya bilder → uppskattning → oberoende validering → uttryckligt
godkännande. Kontrollera sedan verktyget innan nästa plock.

Säg: ”Y beskriver tavlan på flänsen. När tavlan monteras om behöver vi mäta den
relationen igen. Det innebär inte att den fasta kameran, X, har flyttats.”

**Wrong declared board dimensions** behåller den fysiska utskriften men anger 8 %
för stora mått. Bilderna kan ge låg PnP-avvikelse ändå. Den metriska robotkedjan ska
avvisa uppskattningen. Återställ med **Restore measured board dimensions**, registrera
tavlan och ta nya mätningar; återställningen är inget godkännande.

## Pröva en sparad uppskattning utan att återställa ett gammalt godkännande

Efter **Restore nominal sensor output**, öppna **Checks and controlled recovery →
Revalidate a saved estimate**. Välj en tidigare godkänd uppskattning och **Reuse as
inactive candidate**. X och Y ändras inte. Följ **Validate independently** och ge
ett nytt uttryckligt godkännande endast om de nya mätningarna godkänns. Kontrollera
verktyget innan plock. Visa kandidatens ursprung i **Inspect calibration evidence**.

Säg: ”En stabil montering kan spara omtag av samma uppskattning. Vi hoppar inte över
kontrollen: nya oberoende mätningar måste visa att den gamla geometrin fortfarande
gäller. Ett gammalt godkännande räcker inte.”

Flytta sedan kameran och pröva samma sparade uppskattning. Valideringen ska avvisa
den och plock ska förbli blockerat. Följ då nya tavlebilder, uppskattning, validering
och nytt godkännande. En ommonterad tavla kräver också en ny uppskattning av Y.

## Spara för granskning

För att visa tvetydig tavlepose, skapa en separat mätcell med frö **173**. Konfigurera
camera-west och välj **Measurement plan and quality experiments → Nearly frontal
board views**, sedan **Acquire board images**. Inspektera en avvisad post med
`UNRESOLVED_PLANAR_POSE_AMBIGUITY`. Under **Calculation operands and results** finns
båda T_c_t-förslagen, deras pixelavvikelser och skillnaden mellan poängen.
**Improve measurements** följt av **Varied, settled measurements** ger nya bilder;
uppskattningen är fortfarande inaktiv tills oberoende validering och godkännande.

Säg: ”Två olika lägen kan nästan förklara samma plana bild. Vi väljer inte det
bekvämaste svaret. Vi behöver bilder som skiljer alternativen åt.”

Efter ett plock visar **measurement-quality** de faktiska bild/djup- och
överlappskontrollerna. Säg: ”Godkända geometriska kontroller är ingen 99-procentig
sannolikhet. Den här simuleringen uppskattar inte statistisk säkerhet eller ett
felintervall för varje ny punkt.”

Efter **Measure routine references**, välj en sparad referensbild under **Acquired
sensor images**. Gå till **Inspect calibration evidence** och välj samma ID som
`capture`, `surface-detection` och `reference`. **Source** visar det verkliga
anropets sparade Python-kod. **Protocol** visar bild/mask-hash, vald pixel, djupdata,
X, gränser och resultat. För referensen visas både den oberoende uppmätta
baspositionen och den rekonstruerade positionen.

Säg: ”Referenspunkten är bestämd oberoende av den kalibrering vi testar. Python hittar
ytan i bilden och räknar om djupet. Vi jämför resultatet med referensen; vi använder
inte facit som det beräknade svaret. Bildens färgskala visar råvärden och är ingen
egen kvalitetskontroll.”

I en sparad validering, rutinkontroll eller verktygskontroll: välj **Investigate this
evidence**. Python sparar jämförelsen och visar **Check**, **Next measurement** och
**What remains uncertain**. Säg: ”Ett felmönster ger oss en ledtråd, inte en säker
diagnos. Vi ändrar inte kamerans transform för att dölja ett djup- eller verktygsfel.”

Experimentet **Remove required reference tolerance** blockerar godkännandet. **Restore
documented limits** återställer det ursprungliga simuleringsvärdet, men kräver ändå
ny oberoende validering och nytt godkännande. Säg: ”Utan en bestämd tolerans vet vi
inte om resultatet är tillräckligt bra. Vi väljer inte toleransen efter resultatet.”

I en ny, godkänd mätcell: öppna körinställningarna och välj **Missed pick · measured
cell**. Starta **Run a guided pick** och godkänn de vanliga stegen. Robotens rörelse
spelas in, men klossen blir kvar. Öppna posten **pick-outcome** och välj **Investigate
this evidence**. Visa noll överföringar, den nya bilden, originalkommandot och
**INSUFFICIENT_EVIDENCE / UNKNOWN_CAUSE**.

Säg: ”Ett missat plock bevisar inte att kameran sitter fel. Vi behåller X och behöver
separata kontroller av kontakt, verktyg, bild/djup, tid och mekanik. Vi gör inte ett
andra plock automatiskt. Simulatorn modellerar ett missat grepp, inte verklig friktion.”

**Download evidence bundle** innehåller versionsbundna JSON-poster och hashade
PNG/NPY-filer. Delad CLI kan köras utan hårdvara eller en betald modell:

```powershell
uv run --locked python -m tools.calibration reproduce --bundle calibration-evidence.zip
```

Kommandot läser och beräknar om bevis. Det ger inget nytt godkännande och gör inte ett
nytt plock. Källskillnader rapporteras uttryckligen. En inspelning av presentationen
kan visa förloppet, men ersätter inte rådata, oberoende referenser eller kommandokvittot.
