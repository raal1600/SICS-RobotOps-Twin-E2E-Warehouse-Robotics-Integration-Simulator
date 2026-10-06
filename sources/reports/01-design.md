<!-- implementation-status:start -->
> **Implementation status, 2026-10-06:** Integration Lab is verified at audited source 76e6abe: two clean 831-case Linux suites, all 169 MUST criteria, Windows native checks and exact-source publication/Pages verification. Five fresh Blender/manual scenarios remain attributed to unchanged runtime source 9e83fe7. This evidence/status revision requires its own exact-SHA CI, Windows and deployed-build attestation under ADR 0002. Status: DONE at audited C.
> Evidence: GOAL_PROGRESS.md and ACCEPTANCE_REPORT.md in the governance section.
> The research below records design rationale, not real-world robot validation.
<!-- implementation-status:end -->

## Sammanfattning

RobotOps Twin är en implementerad, lokal integrationssimulator för lagerrobotik. Ett förenklat ERP/WMS skapar plockuppdrag. Ett Pythonbaserat integrationslager validerar och lagrar uppdragen, hämtar observationer, begär ett handlingsförslag och skickar typade kommandon till en simulerad robotcell i Blender. En separat verifierare bedömer utfallet innan kundsystemet uppdateras. Den centrala frågan är inte hur en robotarm animeras, utan hur mjukvaran hanterar skillnaden mellan en begärd handling, en kvitterad operation och ett observerat resultat.

Studien kombinerar en riktad genomgång av offentliga primärkällor med ett eget arkitekturförslag och en förhandsdefinierad utvärderingsplan. Underlaget omfattar SICS AI:s rollbeskrivning och HYPER-redovisning, Cognibotics produktionsbeskrivning, CloudGripper/AutoGrasper, R900 samt officiell dokumentation för Blender, OpenAI och integrationsprotokoll. Källorna har olika bevisvärde och hålls därför isär.

**Forskningsdelen redovisar designunderlaget. Aktuell implementationsstatus finns ovan; simulatorresultat är inte fysisk robotvalidering.** Inga prestandasiffror för projektet, säkerhetsgarantier eller resultat om generell intelligens hävdas. Bidraget är ett litet, reproducerbart testsystem där fel efter en fysiskliknande sidoeffekt kan studeras utan verklig robotutrustning.

**Nyckelord:** systemintegration, lagerrobotik, Blender, verifiering, idempotens, återhämtning, observerbarhet, digital-tvilling-inspirerad simulering.

## 1. Syfte, frågeställningar och läsanvisning

Projektet ska visa hur ett kunduppdrag kan följas genom flera system med olika ansvar och olika uppfattningar om vad som har inträffat. Den avsedda användningen är teknisk diskussion, intervjuförberedelse och ett senare portfolioprojekt. Det är inte en beställning från SICS AI och inte dokumentation av företagets interna implementation.

Tre frågor styr designen:

**F1.** Hur kan ett litet system hålla isär affärsuppdrag, modellförslag, robotkommandon och verifierade effekter?

**F2.** Hur kan systemet återhämta sig när kommunikationen försvinner efter att ett objekt redan har flyttats, utan ett omotiverat nytt plock?

**F3.** Vilka relevanta integrationsproblem kan demonstreras i Blender, och vilka slutsatser kräver fysisk utrustning eller tillgång till den verkliga plattformen?

Rapport 1 beskriver forskningsunderlag, arkitektur och testplan. Rapport 2 granskar överförbarheten till en verklig robotmiljö. Rapport 3 är ett samtalsunderlag för diskussion med Axel Kaliff och Per-Eric Olsson. Den som vill förstå huvudidén först kan läsa figur 1, avsnitt 7 och slutsatsen. Kontrakt och utvärderingsprotokoll är till för den tekniska fördjupningen.

Den implementerade operationsvyn visar en interaktiv 3D-cell med maskin och produkter även när ett scenario inte leder till rörelse. Sparat starttillstånd och händelser förklarar stopp; inspelade Blender-poser visar utförda plock. Samma order kan spelas upp igen utan ett nytt plockkommando. Illustrationen är simulatorns facit för betraktaren; verifieraren använder fortfarande en separat WorldObservation. Se implementationens replay-dokumentation i governance-avsnittet.

Den lokala 3D-vyn använder Three.js med kamerakontroller för rotation, panorering och zoom [S22]. Detta är ett visningsval i vår simulator, inte ett påstående om en verklig robots arkitektur.

### 1.1 Vad ordet ”Twin” betyder här

Projektets namn är RobotOps Twin. I denna studie används dock den mer precisa beskrivningen **digital-tvilling-inspirerad integrationssimulator**. Det finns ännu ingen ansluten fysisk tillgång som modellen hålls synkroniserad med. En synlig Blender-scen är därför inte i sig en verifierad digital tvilling av Nowastes anläggning.

Vi definierar en *effekt* som en förändring i simulatorns auktoritativa världstillstånd, exempelvis att objekt O17 flyttas från källåda A till orderlåda B. Att en animation har spelats upp är inte en tillräcklig effektdefinition. Testerna måste kunna inspektera den lagrade världen och effektjournalen.

{{figure:context}}

## 2. Metod och källkritik

### 2.1 Undersökningens karaktär

Detta är en **riktad litteratur- och dokumentstudie med konstruktivt designförslag**. Det är inte en uttömmande systematisk översikt. Urvalet utgår från den aktuella rollen, de namngivna forskarna och de produkter som förekommer i offentliga integrationsbeskrivningar. Sökningen har kompletterats med officiell teknisk dokumentation för föreslagna verktyg.

Kontrolldatum är **1 oktober 2026**. Referensregistret anger organisation eller författare, titel, datum när det är känt, URL och begränsning. Källor utan säkert publiceringsdatum markeras utan datum. En relativ LinkedIn-tidsstämpel omvandlas inte till ett gissat publiceringsdatum.

Arbetsgången var att identifiera relevanta påståenden, kontrollera deras ursprung, härleda ett integrationsbehov och formulera ett eget designbeslut. Författarens beslut redovisas som förslag, inte som fynd om SICS AI. Tidigare research har behandlats som ett sökunderlag och inte som en oberoende källa.

### 2.2 Fyra evidenskategorier

| Kategori | Betydelse i rapportpaketet | Exempel |
|---|---|---|
| Dokumenterat | En identifierbar källa innehåller den beskrivna uppgiften. | En rollannons nämner Pythonintegration. |
| Självrapporterat | Företaget eller projektgruppen beskriver egna egenskaper eller resultat. | HYPER-redovisning och leverantörspress. |
| Eget designförslag | Ett val för RobotOps Twin, härlett men inte kopierat från källorna. | SQLite, kommandokontrakt och testfall. |
| Ej verifierat | Underlag saknas, är otillgängligt eller otillräckligt för slutsatsen. | SICS interna API, säkerhetsarkitektur och modellkod. |

En EU-webbplats kan verifiera att ett projekt och en rapport finns. Det gör inte automatiskt deltagarens tekniska resultat oberoende reproducerade. En tillverkares högsta uppgivna plockhastighet ska inte tolkas som mätt genomströmning hos en viss kund.

Axels examensarbete används med särskild försiktighet: titel och bibliografiskt sammanhang identifierades i föregående research, men fulltexten kunde inte återhämtas i denna publiceringskontroll. Därför återges inga detaljerade metod- eller resultatpåståenden från examensarbetet. Kopplingen till verifiering används som ett avgränsat diskussionstema. [S04]

### 2.3 Publiceringsetik och reproducerbarhet

Alla figurer och arkitekturkontrakt i paketet är egna illustrationer. Inga företagslogotyper, privata e-postmeddelanden eller interna dokument återpubliceras. Referenserna är inspiration och belägg för avgränsade påståenden, inte ett påstående om samarbete eller godkännande.

Text, disposition och publiceringskod har tagits fram med AI-assistans. Projektägaren ansvarar för att läsa och förstå materialet före användning. Rapportpaketet är inte sakkunniggranskat. Källfiler, diagramdefinitioner och byggskript publiceras så att text och figurer går att rätta och regenerera.

## 3. Vad de offentliga källorna faktiskt visar

### 3.1 Rollen: integrationsansvar snarare än enbart modellutveckling

Den granskade Systemingenjör-annonsen kopplar rollen till Python, robotceller och kundernas API:er, PLC:er och WMS/ERP. Den omfattar också LLM/VLM-integration, driftsättning, felsökning, dokumentation och teknisk kunddialog. Industriella protokoll anges som meriterande. Annonsen är ett kravunderlag, inte en fullständig lista över den interna teknikstacken. [S01]

En närliggande annonsversion formulerar erfarenhetskraven annorlunda. Projektet ska därför inte användas för att hävda att alla formella anställningskrav är uppfyllda. Det demonstrerar valda arbetsuppgifter; det ersätter inte yrkeserfarenhet, examen eller ansvar för verkliga leveranser. [S02]

### 3.2 SICS AI:s HYPER-beskrivning

HYPER är registrerat hos CORDIS med projekt-ID 101218436. I deltagarrapporteringen beskriver SICS AI en strukturerad världsmodell och feedbackbaserat lärande samt anger att kärnan inte är en LLM och inte använder reinforcement learning. Rapporten beskriver också robotgränssnitt med kontroll på led- och rörelsenivå. Detta är bolagets redovisning; underlaget räcker inte för att rekonstruera algoritmen. [S03]

För projektet följer ett designkrav: AI-funktionen ska vara en utbytbar komponent med ett uttryckligt in- och utkontrakt. Den ska inte ersättas med en fri textprompt som samtidigt får obegränsad rätt att ändra simulatorn.

### 3.3 Produktionsbeskrivningen från Cognibotics

Cognibotics meddelade den 5 januari 2026 att Nowaste hade **beställt en andra cell** efter den första piloten. Texten tillskriver den befintliga AutoStore-tillämpningen SICS AI-vision samt Juliet & Romeo för rörelse, gripning och transportbandsöverlämning. Källan belägger inte att den andra installationen redan var färdig. Det är leverantörens beskrivning, inte en oberoende driftsrevision eller intern API-specifikation. [S07]

Nowastes eget pressmeddelande från den 26 januari 2024 beskriver en HKM1800 med SICS-programvara i en pilot i produktionsmiljö på Tostarp. Det ger lagerplockning som användningskontext, men ingen rätt att rekonstruera kundens exakta layout eller interna system. Även detta är COMPANY_REPORTED_CLAIM. [S25]

Tillverkaren anger 1,8 m radiell räckvidd över 360 grader, ungefär 10 m² täckning, nära 1 m vertikalt slag och 2 kg nominell respektive 7,5 kg maximal last. Uppgifterna är offentliga tillverkarpåståenden, inte testresultat från RobotOps. [S08] Beskrivningen av basplacerade drivningar och kombinerade serie-/parallelllänkar ger visuell inspiration; vi härleder inga verkliga ledmått eller styrparametrar. [S23] Verktygsväxling för varierande gods är också tillverkarbeskriven, medan våra sex verktyg och deras begränsningar är egna simulatorval. [S24]

HYPER- och produktionsbeskrivningarna behöver inte motsäga varandra. De kan avse olika nivåer, versioner eller tillämpningar. Vårt svar är att skilja mellan uppgiftsnivå och rörelsenivå i designen och be SICS förklara den verkliga ansvarsfördelningen. Två fullständiga styrimplementationer behövs inte i första versionen.

### 3.4 Axel Kaliff, AutoGrasper och R900

CloudGripper/AutoGrasper beskriver ett arbetsflöde där uppgift, återställning, felåterhämtning och datainsamling har separata roller. README-filen anger tillstånden STARTUP, ACTIVE och RESETTING och namnger metoder för normal uppgift respektive återhämtning. Det granskade README-objektets Git-blob är `3cb1da256bc5147ef52a56327da476f110c4e6c2`. Det är forskningsverktyg, inte SICS produktkod. [S05]

R900, med Axel Kaliff som medförfattare, undersöker kostnadseffektiviteten hos autonom datainsamling för robotinlärning. Den granskade arXiv-posten har en reviderad version från 17 september 2025. Studiens automatisering av försök, märkning och återställning motiverar att också vår simulator gör episoder och återhämtning till förstklassiga begrepp. Vi reproducerar inte dess dataset eller modellresultat. [S06]

Axels examensarbetstitel anknyter till verifiering av robotaktioner med en digital tvilling. Examinatorns aktuella akademiska lista anger även hans författarskap i CloudGripper-AutoGrasper. DiVA-fulltexten har fortfarande inte kunnat granskas; endast bibliografisk koppling och öppet repositoryunderlag används. RobotOps gör därför inget anspråk på att reproducera examensarbetets metod eller resultat. [S04][S26]

### 3.5 GPU-resurser och deras roll

ENCCS redovisar arbete med Python/PyTorch och GPU-träning på LUMI. Aixia har offentliggjort en leverans av DGX B200 med drifttjänster till SICS AI. Dessa källor ger stöd för verkligt beräkningsarbete, men fastställer inte var varje kunds inferens körs eller vilket GPU-ansvar den aktuella rollen får. [S10][S11]

Simulatorn behöver ingen B200. Den ska i stället kunna beskriva modellversion, inferensgränssnitt, latens och felutfall. En eventuell framtida GPU-adapter ändrar inte vem som äger ordern eller vem som verifierar ett plock.

### 3.6 Från inspiration till eget beslut

| Källa | Avgränsat fynd | Eget designbeslut | Inte en reproduktion av |
|---|---|---|---|
| Rollannons [S01] | Integration mellan flera system. | Separata kund-, modell- och robotkontrakt. | Företagets exakta stack. |
| HYPER [S03] | Världsrepresentation och robotgränssnitt. | Ett typat Brain-gränssnitt. | Proprietär modell eller AGI. |
| AutoGrasper [S05] | Uppgift, reset och recovery skiljs åt. | Episodmodell och explicita felvägar. | Deras implementation eller data. |
| R900 [S06] | Automatiserade robotförsök. | Reproducerbara scenarier och loggning. | Studiens resultat. |
| Cognibotics / Nowaste [S07][S25] | Rapporterad pilot och beställning av ytterligare cell. | Separat cell- och robotadapter. | Kundens interna API eller exakta cell. |
| Blender [S12–S14] | Scen-API, timers och MCP-verktyg. | Kontrollerad runtime, separat scenförfattande. | Industriell realtidsstyrning. |
| AWS [S17] | Återförsök kräver tydlig identitet och semantik. | Beständig avsikt och avstämning av okänt utfall. | En allmän exactly-once-garanti. |

## 4. Krav och minsta meningsfulla omfattning

### 4.1 Ett litet system med verkliga ansvarsskillnader

Den arkiverade första implementationen har tre syntetiska artikeltyper och ett aktivt plock åt gången. Revision 1.2 har sex produktfamiljer i sex källådor och sex utbytbara verktyg runt en HKM-inspirerad manipulator. HKM-utökningen verifierades med upprepad full acceptans, Blender-tester och publicering vid källrevision ca7798798f916c8130e1833cf16b4d4d3f10d546. Den historiska evidensen ligger under docs/evidence/test-lifecycle-baseline; ACCEPTANCE_REPORT.md redovisar aktuell revisionsstatus. En orderrad omfattar fortfarande ett exemplar; större kvantiteter kräver spårbara deluppdrag. Sparade körningar behåller sina ursprungliga produkt-, scen- och kommandoidentiteter.

Livscykeln skiljer val av robotcell från fel- och observationsscenario. ”Start new test” öppnar ett cellval; endast den HKM-inspirerade cellen kan väljas för nya försök. ”Clear test and retry” behåller försökets nummer och cell men tar efter bekräftelse bort gamla kördata och återställer produkter. ”Delete selected test” tar bort försöket helt; ”Delete all tests” tar bort den bekräftade samlingen. Lediga nummer återanvänds och en tom lista börjar på Test 1. Radering eller rensning avgör inget osäkert plock och skickar inget robotkommando. Ett raderat aktivt försök ersätts inte automatiskt. ADR 0013 beskriver beständig rensningsavsikt, revisionsskydd, anonyma begärandedigester och avgränsad filhantering.

Inför bekräftad datahantering pausar gränssnittet uppdateringar och väntar på pågående läsning av replay och sparad bild. Om läsningen fastnar skickas ingen ändring; användaren kan försöka igen. Serverns skydd för pågående arbete och andra läsares filåtkomst finns kvar.

Systemet ska kunna köras utan externa modellkonton. Blender visar förändringen i världen, men ordern blir inte färdig bara för att animationen slutar. UI:t visar orderstatus, cellstatus, kommandostatus och verifieringsstatus var för sig.

### 4.2 Kravspårbarhet mot rollen

| ID | Arbetsområde | Planerad projektartefakt | Vad som kan bedömas |
|---|---|---|---|
| K01 | Pythonutveckling | Modulärt backend och typade modeller. | Kodstruktur, felhantering och tester. |
| K02 | Kund-API/WMS | Mock-ERP och adapter med kvittenser. | Kontrakt och affärssemantik. |
| K03 | Robotintegration | RobotGateway med Blender-adapter. | Ansvarsgräns och versionshantering. |
| K04 | PLC/cellsignaler | Logisk CellController. | Interlocks och tillstånd, inte PLC-certifiering. |
| K05 | LLM/VLM | Valfri adapter för strukturerade förslag. | Validering, tidsgränser och avvisning. |
| K06 | Driftsättning | Lokal installationsguide och versionsmanifest. | Repeterbar start och konfiguration. |
| K07 | Drift/felsökning | Händelsetidslinje och felinjektion. | Spårbarhet och diagnos. |
| K08 | Tillförlitlighet | Journal, dubblettskydd och reconciliation. | Modellens definierade felantaganden. |
| K09 | Prestanda | Mätning per steg och kötid. | Flaskhalsanalys, inte industriell kapacitet. |
| K10 | Dokumentation/kunddialog | Tre rapporter, kontrakt och demonstrationsmanus. | Förmåga att förklara beslut. |
| K11 | Industriella protokoll | Integration Lab använder verklig AMQP och OPC UA mot en virtuell PLC. | Protokolltrafik belägger inte verklig hårdvara eller säkerhetscertifiering. |
| K12 | AI-stödd utveckling | Versionshanterade ändringar och granskade tester. | Eget ansvar för agentgenererad kod. |

K01–K10 är en forskningsbaserad kravkartläggning. Vilka simulatorfunktioner som har körts och godkänts framgår av ACCEPTANCE_REPORT.md, inte av denna tabell. K11 får inte markeras färdigt för att booleska signaler finns i JSON. Annonsens kärnuppgifter och meriterande områden är utgångspunkt för kartläggningen. [S01][S02]

## 5. Föreslagen systemarkitektur

### 5.1 Komponenter och ägarskap

Arkitekturen är en liten modulär tjänst med separata externa gränser, inte ett stort kluster av mikrotjänster. Ett separat mock-kundsystem och en separat Blenderprocess gör kommunikationsfel möjliga att studera. Modell, verifierare och cellkontroll kan inledningsvis vara moduler i samma Pythonapplikation.

{{figure:architecture}}

| Del | Äger | Får inte göra |
|---|---|---|
| Mock ERP/WMS | Order, artikelregister och kundens kvittens. | Skriva robotleder eller modellens interna tillstånd. |
| Integrationslager | Uppdrag, avsikt, försök och rapportering. | Tolka timeout som bevis för utebliven effekt. |
| Brain-adapter | Ett handlingsförslag och modellmetadata. | Exekvera kod i Blender eller godkänna sig själv. |
| Validator | Kontrakt, aktualitet och operationella gränser. | Påstå att logiska kontroller är funktionell säkerhet. |
| CellController | Simulerad tillgänglighet, stopp och signaler. | Återstarta rörelse automatiskt efter reset. |
| RobotGateway | Kommandostatus och adapterförmågor. | Dölja skillnader mellan stödda och ostödda kommandon. |
| Blender-runtime | Simulatorns värld och effektjournal. | Låta UI eller modell manipulera världen direkt. |
| Verifierare | Bedömning baserad på observationer. | Anta att sänd kvittens innebär lyckad uppgift. |
| Test-orakel | Jämförelse med fullständigt simulatortillstånd. | Ge den ordinarie beslutsvägen obegränsad facitåtkomst. |

### 5.2 Två arkitekturnivåer, en första implementation

Det logiska gränssnittet kan uttrycka både `PickIntent` och `JointTrajectory`, men första implementationen ska endast utföra en avgränsad `PICK_AND_PLACE`-uppgift via fördefinierade, validerade rörelsesegment. En kapabilitetsförfrågan anger vad adaptern faktiskt stöder. En ostödd ledtrajektoria ger ett tydligt fel, inte en approximativ animation som låtsas vara motsvarande styrning.

Senare kan en lednivåadapter införas med lednamn, tidsatta waypoints och explicit robotmodell. Det är ett separat integrationsarbete med egna tester. Gemensamt affärskontrakt kan minska ändringar i ERP-delen, men gör inte ett hårdvarubyte plug-and-play.

### 5.3 Driftmiljö

Snabbprofilen använder webbläsare, Python, SQLite och syntetisk eller Blender-baserad runtime. Integration Lab använder PostgreSQL för applikationstillstånd, en transaktionell outbox, verklig RabbitMQ/AMQP, en separat Python-edge med beständig inbox och verklig OPC UA till en virtuell PLC. Runtime-journal, PLC-journal och värld lagras lokalt enligt den dokumenterade felmodellen. En syntetisk WMS-tjänst tar emot verifierade resultat över REST. En produktionsanslutning till ett verkligt ERP är fortfarande ett separat integrationsarbete.

{{figure:integration-lab}}

Guided Console sparar 22 avgränsade steg och revisionsskyddade beslut. Ingen databastransaktion väntar på användarens svar. **AUTHORIZE ROBOT EXECUTION** måste passeras innan simulerad rörelse får starta. WebSocket-strömmen är skrivskyddad. Källkod, protokolldata och verkligt respektive simulerat ansvar visas per steg. [Implementerad labbprofil och körkommandon](https://github.com/raal1600/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/blob/main/docs/integration-lab.md) beskriver processer och återhämtning; [kravgranskningen](https://github.com/raal1600/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/blob/main/docs/integration-lab-requirements.md) skiljer implementation från ännu ej styrkt slutacceptans.

GitHub Pages används endast för rapporter, diagram och nedladdningar. Pages kör inte Pythonbackend eller Blender. En framtida inspelad demo ska märkas inspelad och inte presenteras som levande robottelemetri. [S19]

## 6. Datakontrakt och tillstånd

### 6.1 Identiteter som inte får blandas ihop

`order_id` identifierar kundens order. `job_id` identifierar den affärseffekt som efterfrågas. `command_id` identifierar ett specifikt exekveringsförsök. `event_id` används för mottagardubbletter. `scene_epoch` identifierar en sammanhängande simulatorvärld och ändras vid återställning av scenen. En scenåterställning får inte radera tidigare orderhistorik eller få gamla kommandon att bli giltiga igen.

Återleverans av samma orderbegäran använder samma idempotensnyckel. Samma nyckel med annat innehåll avvisas som konflikt. Ett nytt försök efter ett verkligt misslyckande får egen försöksidentitet men behåller kopplingen till samma uppdrag. Skillnaden mellan begäran och avsikt är central i designen. [S17]

### 6.2 Implementerat kommando

Det fullständiga, versionshanterade kontraktet finns i `contracts/schemas/RobotCommand.json`. Det innehåller stabil order-, jobb-, plan-, kommando- och observationsidentitet, scenepok, cellgeneration samt `product_id`, källa, destination och en typad `target_pose` med meter, koordinatram och kalibrering. JSON är strikt data; okända fält och godtycklig kod avvisas. Det är vårt simulator-API, inte SICS AI:s API.

Valideringen kontrollerar bland annat tillåten kommandotyp, ändliga tal, rätt koordinatsystem, korrekt objekt, rimliga gränser, kompatibel kalibrering och tillräckligt aktuell observation. Kvaternionen kontrolleras mot en dokumenterad normtolerans. Toleranserna är egna simulatorparametrar och får inte kallas industriellt säkra.

### 6.3 Normativa API-gränser

GOAL.md, PROJECT_PLAN.md och contracts/ beskriver implementationens gränser.
POST /v1/wms/tasks skapar en guidad session. POST /integration/sessions/{id}/authorize
utför ett revisionsskyddat steg; /reconcile undersöker samma ursprungliga kommando.
GET /integration/sessions/{id}, dess /live-resurs och /stream-WebSocket är skrivskyddade.
Order-, jobb-, tidslinje-, evidens-, /health- och /metrics-resurser finns kvar.
De äldre POST /orders och /jobs/{id}/run finns för lokal kompatibilitet men avvisas
i labbprofilen, där hela den guidade protokollkedjan krävs.

Samma idempotensnyckel och payload återger samma order. Ändrat innehåll ger
konflikt. Journalens frånvaro bevisar inte i sig utebliven effekt.

### 6.4 Uppdragstillstånd och celltillstånd

{{figure:state}}

Den normativa normalvägen är RECEIVED → VALIDATED → PLANNING →
READY_TO_EXECUTE → EXECUTING → VERIFYING → COMPLETED för plockuppdraget.
I den guidade kedjan stannar orderns affärsstatus i RECONCILING tills samtliga
verifierade plock har beständiga WMS-kvittenser och steg 21 sparar ERP-utfallet.
Robotresultat, sensorverifiering, WMS-kvittens och ERP-status är separata fakta.
Den syntetiska affärsmodellen är ingen leveransgaranti för ett verkligt kundsystem.

UNKNOWN_OUTCOME kan endast lösas via RECONCILING och lagrad evidens.
Otillräckligt eller motstridigt underlag ger REQUIRES_INTERVENTION, aldrig
påhittad framgång. Timeout är inte bevis för FAILED.

REQUIRES_INTERVENTION pausar nya plock men tillåter en uttrycklig begäran om ny
observation för samma kommando. Via RECONCILING kan tillräcklig ny evidens lösa
utfallet; annars pausas uppdraget igen. Varje bedömning sparas. Omstart eller
granskning av evidens öppnar inte intervention automatiskt, och inget nytt plock
skickas vid avstämningen. Detta är vårt simulatorval enligt ADR 0008.

Cellen har READY, BUSY, FAULTED, ESTOP_LOGICAL, RESETTING och OFFLINE.
Reset bevisar inte oförändrad värld. Osäkra uppdrag behöver ny observation och
avstämning. Stoppet är logiskt, aldrig en säkerhetsklassad funktion.

## 7. Kärnfallet: utfört plock, förlorad kvittens

### 7.1 Varför ett återförsök kan vara fel

Anta att robotadaptern flyttar ett objekt, men att nätverket bryts innan integrationstjänsten får svaret. Klienten ser bara en timeout. Två förlopp är då förenliga med samma observation: ingenting utfördes, eller allt utfördes men svaret försvann. Utan mer information går det inte att välja ett säkert nytt plock enbart utifrån timeouten.

{{figure:ack-loss}}

Lösningen kombinerar beständig avsikt, kommandoregister och observation efter handling. Den utlovar inte en universell exactly-once-egenskap. Ett databaslås och en robotrörelse är inte en gemensam atomär transaktion.

### 7.2 Föreslaget återhämtningsförlopp

Integrationslagret lagrar avsikten före sändning. Blender-adaptern lagrar kommandots ID och innehållshash före effekt. När kvittensen uteblir markeras uppdraget som osäkert. Integrationen frågar efter samma kommando och begär en färsk observation. Om journal, epok och observerat objektläge ger tillräckligt stöd kan verifieringen fortsätta utan ett nytt plock.

Om journalen säger slutfört men objektet inte kan lokaliseras är det en konflikt som kräver utredning, inte tillåtelse att välja den mest bekväma uppgiften. Om journalen gått förlorad och bilden är skymd kan korrekt beteende vara att stoppa automatiseringen och visa osäkerheten.

### 7.3 Omstarter och delvis genomförda handlingar

En omstart av integrationstjänsten får inte nollställa robotens värld. Den återläser uppdrag och utgående meddelanden från beständig lagring. Vid avbrott under sändning gör den avstämning innan nya rörelseförslag tillåts.

En omstart av Blender är svårare. Scenens senaste sparade fil kan ligga efter effektjournalen. Första versionen ska därför antingen bevara en konsistent scenögonblicksbild tillsammans med logiskt stegnummer eller uttryckligen markera att världen inte kan återställas säkert. Vid inkonsistens skapas en ny scene_epoch och pågående uppdrag kräver manuell granskning. Att tyst läsa en gammal .blend-fil och fortsätta skulle dölja felet.

Ett uppdrag kan också avbrytas när objektet sitter i griparen. Verifieraren måste därför skilja mellan rätt destination, kvar i källan, fäst i verktyget och oklart läge. Återhämtning är inte alltid samma sak som att börja från början.

## 8. Observation, modell och verifiering

### 8.1 Fyra representationer av världen

Simulatorn äger det verkliga tillståndet inom modellen, `x`. Sensoradaptern producerar observationen `y`. Brain-komponenten kan hålla en intern uppskattning eller ett minne, `b`. ERP-uppdraget definierar det önskade tillståndet, `g`. Dessa får inte blandas ihop.

En förenklad egen modell är:

`y_t = h(x_t, calibration, occlusion, noise)`

`proposal_t = planner(y_t, b_t, g)`

`x_(t+1) = simulator(x_t, validated_command_t)`

`verdict = verifier(y_before, y_after, command_journal)`

Uttrycken beskriver ansvar, inte en reproduktion av SICS lärandealgoritm. En klassisk databas med objektpositioner är inte automatiskt en inlärd världsmodell.

{{figure:worlds}}

### 8.2 Test-orakel respektive ordinarie verifierare

Test-oraklet får läsa fullständig simulatorinformation för att avgöra om systemets bedömning var rätt. Den ordinarie verifieraren får bara de sensorliknande uppgifter som scenarioinställningen medger. Annars blir testet cirkulärt: samma funktion flyttar objektet och intygar sedan att den själv gjorde rätt.

Även dessa två vägar delar simulatorns antaganden. Separationen minskar en viss typ av logiskt fel, men gör inte verifieringen oberoende av simuleringsmodellen. Korrekta metadata är inte ett bevis för korrekt synsystem i en verklig lagercell.

### 8.3 Koordinater och tid

Alla positioner uttrycks i meter, vinklar i radianer och orienteringar i en angiven konvention. En enkel koordinattransformation skrivs `p_cell = R × p_camera + t`. Räkneexempel: utan rotation ger kamerakoordinaten `(0,10; 0,20; 0,30)` och förskjutningen `(0,40; 0; 0,80)` cellkoordinaten `(0,50; 0,20; 1,10)` meter. Detta är ett pedagogiskt exempel, inte robotkalibrering.

Varje observation har fångsttid, mottagningstid och scensteg. Väggklocka används för mänskligt läsbara loggar; monotona tidsmått används för lokala tidsgränser. Simuleringstid hålls separat från verklig elapsed time. Ett bildresultat från en tidigare scene_epoch avvisas även om objektets namn råkar vara oförändrat.

### 8.4 Deterministisk baslinje och valfri modell

Baslinjen gör ett reproducerbart val bland tillåtna objekt och rörelsesegment. Den tränar ingen modell. En valfri LLM/VLM-adapter kan ge ett strukturerat förslag, men schemakorrekthet garanterar inte semantisk korrekthet. OpenAI dokumenterar strukturerade utdata och särskild hantering av exempelvis avvisade svar. [S16]

Implementerade felvägar är timeout, okänd objektidentitet, felaktig destination och otillräcklig observation. Avvisat externt modellsvar hör till den valfria modelladaptern som inte är implementerad. Dessa ger ett synligt avbrott eller en dokumenterad alternativ policy. Ett självrapporterat confidence-värde ska inte behandlas som kalibrerad sannolikhet för ett lyckat grepp.

## 9. Blender, MCP och operationella gränser

### 9.1 Scen och rörelse

Den arkiverade baslinjen använder en stiliserad kartesisk maskin, två lådor och tre produktkuber. Nya världar i revision 1.2 använder en originalbyggd HKM-inspirerad hybridmanipulator och en rikare lagercell: sex källådor, varierande produktgeometri, sex verktygsdockor, transportband, inhägnad och tre kameror. Baslinjens gamla scener och inspelningar behåller sin ursprungliga form; en ny standardprofil ändrar inte sparad historik.

{{figure:hkm-cell}}

`HKM_INSPIRED_VISUAL_KINEMATICS_V1` är vårt namn på en deterministisk avbildning från TCP-pose till sammankopplade visuella länkar. Matematiken finns i `robotops/hkm_geometry.py`; den gör inga anspråk på verklig HKM-IK. Version-2-inspelningar innehåller utvärderad position, quaternion, skala, fas, synlighet och verktygs-/objektanknytning. Blender- och webbläsarvyn använder samma semantiska objektidentiteter. Replay är läsning av inspelad evidens, aldrig en väg tillbaka till robotkommandon.

Blenders Python-API stöder programmatisk åtkomst till objekt, scen och animation, vilket passar denna avgränsade syntetiska värld. [S27] Kontaktkrafter, deformation och riktiga sugkoppskrafter simuleras inte. PyBullet dokumenterar fysik, ledkroppar, IK och kollisionsfunktioner; Isaac Sim dokumenterar robotrörelse och sensormodeller. De är relevanta jämförelser om sådan validering senare blir ett krav, men införs inte som nya beroenden här. [S28][S29][S30]

### 9.1.1 Verktygsval och synlig förberedelse

Den kanoniska katalogen `robotops/robotics/catalogue-v1.json` beskriver våra sex produktfamiljer, massa/geometri och sex gripverktyg. Tabellen nedan genereras direkt från samma data. P/C är kandidater; separat kontroll av produktens konservativa maximala fixturmassa, geometri och tillgänglighet kan ändå utesluta ett verktyg. Poäng, avvisningsskäl och stabil rangordning sparas i planen och visas under ”Why this tool?”. Integrerad köracceptans redovisas separat från att katalogen existerar.

{{figure:product-tool-compatibility}}

Verktygsväxling är en förberedelse inom det ursprungliga PICK_AND_PLACE-kommandot. Rackplats, monterat verktyg och kontrollsteg sparas beständigt. Ett verktygsbyte ökar inte antalet produktförflyttningar. Saknat begärt verktyg stoppar före produktens effekt; redan korrekt verktyg ger ett explicit no-change-beslut. `tool_showcase` kör alla sex produktfamiljer med deras föredragna verktyg och verifierar varje jobb innan nästa börjar.

{{figure:tool-preparation}}

### 9.1.2 Trajektoria, arbetsområde och ramar

Planeringen innehåller förberedelse, lodrät ansats, grepp/kvittens, lyft, hög syntetisk överföringsnivå, placering, lossning/kvittens och reträtt. Deterministisk smoothstep ger läsbar acceleration utan att imitera tillverkarens cykeltid. Simuleringstid och presentationshastighet hålls skilda från faktisk pipeline-latens och UTC-händelser.

Den egna konservativa geometrikontrollen samplar arbetsområdet och testar segment mot expanderade hindergränser, provar ett ändligt antal alternativa vägar och avvisar om ingen väg fungerar. Synliga statiska objekt och hindergränser kommer från samma geometri; även observerade produkter, last och parkerade verktyg kontrolleras. Endast registrerad lodrät dockning till rätt verktyg får undantag för avsiktlig kontakt. Rotationsrörelser får en konservativ svept volym. Kontrollen validerar inte verklig robotkollision, länkarnas kontaktfysik eller säkerhet. Runtime kontrollerar oberoende identitet, scenepok, källa, verktyg, kalibrering och begränsad trajektoria före effekt. Sensorramar och celltelemetri märks uttryckligen; en renderad kamerabild bevisar inte att datorseende har körts.

{{figure:frames}}

### 9.2 Blender-runtime och trådar

Blenders dokumentation varnar för osäker användning av Pythontrådar. Scenändringar ska inte göras godtyckligt från en långlivad bakgrundstråd. Timers ger ett API för schemalagda anrop. [S13][S14]

Den implementerade adaptern använder i stället en tidsbegränsad Blender-batchprocess med ett fast Python-skript och typade JSON-filer. Scenändringar sker på Blenders huvudtråd. RUNNING journalförs före start; scenfilens hash och svarets identitet kontrolleras innan checkpointen godkänns. Saknat eller korrupt svar leder till osäkerhet utan omkörning. Blender-version och skripthash finns i runtime-manifestet. ADR 0001 dokumenterar valet; ingen långlivad nätverksbrygga krävs. CPU-versionen är Blender 5.2.1 LTS. [S21]

På Windows startar den avgränsade processen med Blenders dokumenterade `--qos high` för att använda prestandakärnor på hybridprocessorer. [S31] Detta är ett processlokalt simulatorval; det ändrar inte Windows-policy, renderkvalitet, inspelningsfrekvens eller den befintliga tidsgränsen. Runtime-manifestet anger `cpu_qos`. Upprepade oförändrade synlighetsvärden skrivs inte om under animering, men verkliga synlighetsändringar behålls i sparade keyframes. Lokala prestandatester är inte validering av robotens fysiska genomströmning.

### 9.3 MCP hör till utvecklingsmiljön

Blender Lab beskriver en MCP-server med ett separat tillägg och varnar för att LLM-genererad kod kan köras utan dataskyddsräcken. Den kontrollerade sidan anger Blender 5.1 eller senare för just denna integration. [S12]

Codex kan ansluta till MCP-servrar. Det kan användas för kodarbete, scenförfattande och granskning; den aktuella runtime-adaptern använder det inte, inte som en säkerhetsklassad regulator. [S15]

{{figure:trust}}

Under utveckling kan en agent föreslå Blenderkod i en isolerad miljö. Under körning accepterar robotadaptern endast det definierade kommandoschemat. Runtime erbjuder ingen `exec`, ingen godtycklig filåtkomst och inga modellvalda externa adresser. API-nycklar ligger utanför repot och aldrig i den publicerade webbsidan.

### 9.4 PLC och stopp

Cellmodellen har READY, BUSY, FAULTED, ESTOP_LOGICAL, RESETTING och OFFLINE samt generationsnummer. Runtime kontrollerar källobjekt och destination mot det typade kommandot. Före start måste definierade förvillkor vara uppfyllda. Signalerna behöver aktualitetskontroll; ett gammalt READY räcker inte.

Integration Lab implementerar OPC UA-klient/server-trafik med anslutning, browse, prenumeration och metoder för SubmitJob, ursprunglig status och resultatkvittens. Informationsmodell och återstartssemantik dokumenteras i labbguiden. Ett REST-svar från edge är inte i sig bevis för OPC UA; spåret innehåller de underliggande metodsvaren och datanotifikationerna. PLC-till-runtime-länken märks **simulated controller interface**. OPC Foundations åtskillnad mellan informationsmodell och kommunikationstjänster är relevant för denna gräns. [S18]

Stoppknappen i demonstrationen är **en simulerad operationell spärr**, inte ett nödstopp med verifierad säkerhetsfunktion. Projektet ska inte anslutas till fysisk robotutrustning med denna logik som skyddssystem.

## 10. Utvärderingsprotokoll och genomförd acceptans

Den ursprungliga forskningsplanen nedan innehåller även framtida experiment. Den normativa obligatoriska sviten definieras av SUCCESS_CRITERIA.md. ACCEPTANCE_REPORT.md kopplar varje MUST till aktuella kommandon, tester och artefakter. T07 (extern ERP-outbox), kontinuerligt stopp mitt i rörelse i T10, partiellt grepp i T12 och jämförande fröexperiment är uttryckligen tillägg; de har inte körts som sådana. Batch-runtime simulerar ingen säker realtidsavbrytning.

### 10.1 Hypoteser och jämförelse

**H1:** Under det definierade kvittensbortfallsfallet ska journal plus avstämning undvika ett extra plockförsök som saknar stöd i observerat tillstånd.

**H2:** En verifierare med begränsad observation ska ibland lämna utfallet oavgjort, i stället för att felaktigt markera uppdraget slutfört.

**H3:** En tjänsteomstart ska inte orsaka att en redan verifierad affärseffekt utförs igen när endast ERP-kvittensen återstår.

Hypoteserna är prövbara inom simulatorns felmodell. De är inte testresultat. En medvetet naiv återförsöksstrategi kan användas som jämförelse i en isolerad testvariant. Båda varianterna ska då möta samma scener och felinjektioner. Baslinjen får inte köras mot fysisk utrustning.

### 10.2 Scenarier och godkännandekriterier

| ID | Injicerat eller kontrollerat fall | Förväntad egenskap |
|---|---|---|
| T01 | Normalt plock | Ett objekt i rätt destination; korrekt ERP-kvittens. |
| T02 | Samma order skickas två gånger | Samma uppdrag återfås; ingen extra effekt. |
| T03 | Samma nyckel, ändrat innehåll | Konflikt avvisas före rörelse. |
| T04 | Kvittens tappas efter effekt | Okänt utfall synliggörs; avstämning utan blint nytt plock. |
| T05 | Kommando avvisas före start | Ingen effekt; tydlig orsak och kontrollerat nytt försök. |
| T06 | Integrationstjänsten startas om | Beständig historik återläses och pågående avsikt stäms av. |
| T07 | ERP otillgängligt efter verifiering | Kundsynk återförsöks, inte robotplocket. |
| T08 | Objektet skymt efter rörelse | Ingen falsk slutsats från att objektet inte syns. |
| T09 | För gammal observation eller fel epok | Planen avvisas. |
| T10 | Stopp under rörelse | Ingen automatisk fortsättning efter reset. |
| T11 | Felaktigt modellförslag | Validatorn hindrar exekvering och loggar orsaken. |
| T12 | Delvis plock, objekt i griparen | Delutfallet registreras; återstart sker inte från fel antagande. |
| T13 | Motstridiga journal- och sensoruppgifter | Ärendet eskaleras som konflikt. |
| T14 | Andra exekveraren försöker ta samma cell | Ensam exekveringsrätt upprätthålls eller starten avvisas. |
| T15 | Blender omstart med inkonsistent snapshot | Ny epok och granskning; inget tyst återspel. |
| T16 | Observation med fel koordinatenhet | Kontraktsfel upptäcks före exekvering. |

Ett valfritt framtida experiment föreslås använda tio namngivna scenfrön per scenario, med dokumenterade objektplaceringar och felpunkter. Antalet är en praktisk startpunkt, inte en statistisk styrkeberäkning. Deterministiska fall ska också testas vid flera gränser i tillståndsövergången, inte bara med flera slumpfrön.

### 10.3 Mått och invarianta villkor

**Duplicerad effekt:** antal uppdrag där fler effekter än beställt har inträffat, dividerat med antal uppdrag.

**Falskt slutförande:** antal uppdrag märkta slutförda trots att test-oraklet visar fel slutläge, dividerat med antalet slutförda uppdrag. Om nämnaren är noll redovisas måttet som ej tillämpligt.

**Oavgjorda utfall:** antal uppdrag där verifieraren saknar tillräckligt underlag. Ett lägre värde är inte automatiskt bättre om det köps genom fler felaktiga godkännanden.

**Återhämtningstid:** tid från upptäckt fel till verifierad lösning eller eskalering. Rapportera både simulerade steg och verklig elapsed time, med maskin- och versionsuppgifter.

Invarianta villkor är bland annat att gamla scene_epoch-kommandon inte körs, att endast en aktör ändrar roboten åt gången och att färdig kundorder bygger på en lagrad verifieringspost. Noll observerade fel i ett litet prov ska inte tolkas som noll verklig felrisk.

### 10.4 Reproduktionspaket

Varje körning ska kunna exportera Git-commit, konfiguration, scene_hash, seed, schema- och modellversion, inskickade kommandon, händelseföljd, observationer, orakelutfall och mätvärden. Modellkörningar redovisas separat från den deterministiska baslinjen. Nätverkskostnader och externa anrop ska vara synliga och begränsade.

Ett misslyckat experiment sparas lika noggrant som ett lyckat. Presentationen får inte välja endast vackra videosekvenser och dölja resten av testpopulationen.

## 11. Genomförande, dokumentation och underhåll

### 11.1 Ursprunglig byggordning och aktuell status

Etapperna nedan beskriver den ursprungliga forskningsplanen. P0–P5 i PROJECT_PLAN.md är implementerade; P6 är valfri och ej implementerad. P7 omfattar slutlig acceptans och publicering. Fullständig aktuell status står i rapportens statusruta. Utökade experiment i avsnitt 10 är inte automatiskt genomförda genom att kärnan finns.

**Etapp A: kontrakt och testbar kärna.** Skapa modeller, beständig uppdragslogg, kundmock och en robotstub utan grafik. Godkänn T01–T07 innan scenarbete blir huvudfokus.

**Etapp B: Blender som värld.** Inför scenmetadata, begränsad runtime, observation och verifiering. Demonstrera ett normalt plock och ett kvittensbortfall med samma orderflöde.

**Etapp C: svåra fel.** Lägg till stopp, stale observation, delutfall, epoker och restart-konflikter. Dokumentera vilka fall som ännu inte kan lösas automatiskt.

**Etapp D: tillägg.** Lägg till valfri bildmodell eller ett verkligt lokalt OPC UA-gränssnitt först när baslinjen är stabil. Fotorealism, komplex fysik och flera robotar prioriteras sist.

### 11.2 Implementationens struktur

Den aktuella målstrukturen finns i PROJECT_PLAN.md: apps/, robotops/domain/,
robotops/workflow/, robotops/brain/, robotops/robot_gateway/, robotops/cell/,
robotops/blender/, robotops/observation/, robotops/verification/, contracts/ och
tests/{unit,contract,integration,e2e}/. GOAL_PROGRESS.md redovisar vad som finns
nu och ACCEPTANCE_REPORT.md redovisar verifierad evidens. Dokumentationsbygget
hålls separat från runtime. Se ADR 0001 för den begränsade processadaptern.

### 11.3 Definition av färdig demonstration

Demonstrationen är färdig först när en annan person kan följa startinstruktionen, skapa en order, se en verklig scenändring, följa dess ID genom tidslinjen och återköra kvittensbortfallsfallet. Ett statusmanifest ska ange genomförda tester och kända begränsningar. Skärminspelning är en reservväg, inte en ersättning för testbarhet.

## 12. Diskussion, begränsningar och slutsats

Det mest överförbara i projektet är gränssnitten och resonemanget om osäkerhet: affärsavsikt, exekveringsförsök och effekt behöver olika identiteter och bevis. Den minst överförbara delen är den förenklade världen. Fästning av ett objekt i en gripare kan inte belägga robust gripning, och en kontroll i SQLite kan inte belägga säker robotrörelse.

Det finns risk för gemensamma modellfel mellan simulator och verifierare. Scenarierna är få, produkter förenklade och hårdvarans dynamik saknas. En framtida verklig integration kräver nya adapterspecifikationer, riskbedömning, fysisk kalibrering, driftsättningsprov och verksamhetsförankring. Rapport 2 utvecklar dessa gränser.

**Slutsatsen är att projektet är motiverat som ett avgränsat integrations- och återhämtningstest, inte som en kopia av SICS AI:s robotbrain.** En liten demo med ärlig osäkerhet, spårbara beslut och reproducerbara fel är vetenskapligt mer användbar än en större animation som ger sken av verifierad fysisk förmåga.

Den fortsatta diskussionen bör pröva designens antaganden: var den verkliga plattformens gränser går, vilka fel som är vanligast och vilken evidens som krävs för att ett plock ska räknas som lyckat. Den aktuella publikationsrevisionen länkar verifierad simulator-evidens via ACCEPTANCE_REPORT.md. Den redovisar inga experimentella resultat för fysisk robotprestanda eller generell intelligens.

## Implementerat undersökningsflöde (2026-10-05)

Arbetsytan prioriterar körning, synligt resultat och en uttrycklig undersökning.
En kort scenariobeskrivning säger vad operatören ska titta efter. Avvikande resultat
markeras utan att automatiskt täcka cellen. Panelen skiljer symptom, innehållet i
sparade bevis och möjliga förklaringar. Den bedömda observationen väljs med dess ID;
animationen och den aktuella felväljaren får inte ersätta evidens. Tidslinjen är
sekundär och höjdbegränsad. API-anrop, JSON-export och riktiga kod-/loggsökvägar
stöder fortsatt teknisk undersökning. Återgång bevarar uppspelningens sammanhang.
Detta är egen SIMULATOR_DESIGN, inte ett nytt påstående om SICS AI:s produkt.

{{figure:investigation}}
