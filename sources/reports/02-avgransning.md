<!-- implementation-status:start -->
> **Implementation status, 2026-10-04:** The HKM-inspired six-product/six-tool cell, bounded Blender runtime, deterministic tool selection, geometric preflight and rotation-aware read-only replay are implemented. Targeted checks include real Blender integration and 107 UI checks, plus browser six-tool and uncertain-outcome workflows. The prior release and fresh eaf35b4 baseline remain archived; this enhancement awaits repeated full acceptance and exact-commit CI/publication evidence. Status: NOT DONE.
> Evidence: GOAL_PROGRESS.md and ACCEPTANCE_REPORT.md in the governance section.
> The research below records design rationale, not real-world robot validation.
<!-- implementation-status:end -->

## Sammanfattning

Den här rapporten skiljer **RobotOps Twins implementerade simulator** från dels en generell industriell robotcell, dels den begränsade bild av SICS AI:s miljö som finns i offentliga källor. Dessa två jämförelseobjekt är inte samma sak. Offentlig information räcker inte för att beskriva företagets fullständiga interna system.

Simulatorn ska efterlikna informationsflödet från kundorder till verifierat plock och återkoppling. Den ska bevara vissa integrationsproblem: dubbletter, osäkra utfall, återhämtning, separata systemägare och motstridiga observationer. Den ska däremot förenkla robotmekanik, sensorsystem, säkerhet, produktvariation, nätverk och driftorganisation.

**Det som demonstreras är programvarans beteende under definierade simuleringsantaganden.** Det är inte ett bevis för fysisk säkerhet, kommersiell driftsäkerhet, ett fungerande SICS-gränssnitt eller generell intelligens. Aktuell implementationsstatus och kvarvarande arbete redovisas i statusrutan ovan.

## 1. Jämförelsens tre nivåer

Vi använder tre nivåer för att undvika att generella branschbegrepp tillskrivs ett enskilt bolag.

**Nivå A: dokumenterad offentlig uppgift.** Exempelvis anger SICS rollannons kundintegration, medan Cognibotics rapporterar en första pilot och en beställning på ytterligare Nowaste-cell. Uppgifterna citeras och attribueras. Att ett företag offentligt framför ett påstående gör det inte till oberoende validerad prestanda. [S01][S07]

**Nivå B: generell integrationsfråga.** Exempelvis måste ett system skilja mellan förlorad kommunikation och en känd utebliven sidoeffekt. Det är en fråga om distribuerad systemdesign, inte ett fynd om hur SICS har implementerat sin lösning. [S17]

**Nivå C: vårt simulatorval.** SQLite, en Blender-arm, en deterministisk Brain-adapter och ett visst tillståndsdiagram är egna beslut. De ska kunna ändras utan att källorna ändras.

Jämförelsen är alltså inte en omvänd konstruktion av SICS AI:s produkt. Den identifierar vilka aspekter en liten demonstrator kan representera och var motsvarigheten upphör.

{{figure:boundary}}

## 2. Vad vi vet, vad vi förenklar och vad vi inte vet

### 2.1 Affärssystem och integration

| Aspekt | Offentlig eller generell verklighetsbild | RobotOps Twins mål |
|---|---|---|
| Kundflöde | Rollen omfattar kundens API/WMS/ERP. [S01] | Sex syntetiska SKU-familjer i revision 1.2; gamla tre-SKU-körningar bevaras. Ett plock per orderrad. |
| Affärsregler | Exakta kundregler är inte offentliga. | En enkel regel: rätt exemplar till rätt orderlåda. |
| Integration | Leverantörsmaterial beskriver lagerstyrning runt robotcellen. [S07] | Separat kundadapter och kvittenskontrakt. |
| Inventering | Verklig redovisning, reservation och korrigering är inte kartlagda. | Förenklad reservations- och saldomodell utan bokföring. |
| Kommunikation | Det faktiska protokollet och garantierna är okända. | Lokala API:er med injicerad fördröjning och kvittensförlust. |

En mock kan visa hur kontrakt hanteras. Den kan inte visa att alla verkliga affärsregler är förstådda. Returer, substitution, batcher, förpackningshierarkier, lagersaldokonflikter och flera samtidiga kunder ligger utanför den första versionen.

Ett lyckat plock kan också vara olika saker i olika affärsprocesser: flyttat objekt, scannad artikel, klar orderrad eller skickklar försändelse. Simulatorn ska därför uttryckligen definiera sin sluttillståndsregel. Den bör inte använda ordet ”levererad” för en artikel som bara har flyttats mellan två lådor.

### 2.2 AI, robot och rörelse

| Aspekt | Offentlig uppgift eller kunskapslucka | Simulatorns avgränsning |
|---|---|---|
| Robotbrain | HYPER beskriver en proprietär modell. [S03] | Ett gränssnitt, inte en återimplementation. |
| Modellstyrning | Offentliga texter beskriver olika kontrollnivåer. [S03][S07] | Typat verktygs-/TCP-/trajektoriekontrakt; inga verkliga HKM-ledkommandon. |
| Robotmekanik | Tillverkaren beskriver hybridkinematik. [S08][S23] | Original HKM-inspirerad visuell mekanism; inga exakta CAD-, dynamik- eller prestandapåståenden. |
| Gripning | Tillverkaren beskriver automatisk verktygsväxling. [S24] | Sex egna syntetiska verktyg och regler för fästning/lossning; ingen kontaktfysik. |
| Perception | Den exakta sensorkedjan är inte offentlig. | Deterministisk WorldObservation, separat märkt celltelemetri; rendering är inte bildanalys. |
| Inlärning | Algoritm, data och vikter är inte tillgängliga för denna studie. | Ingen träning i baslinjen; versionshanterad planeringslogik. |

En animation kan vara begriplig utan att dess moment, kontaktkrafter eller ledhastigheter motsvarar en verklig robot. Det är tillåtet i en integrationsdemo om det är tydligt deklarerat. Problemet uppstår när visuellt övertygande rörelse används som underlag för påståenden om dynamisk noggrannhet.

Tabellen beskriver den implementerade simulatoravgränsningen för revision 1.2. Riktade tester kör sex verktyg och produktfamiljer i faktisk Blender, men full upprepad acceptans och publicering för slutlig källrevision återstår; ACCEPTANCE_REPORT.md avgör slutstatus. Verktygsbyte under samma journalförda kommando ändrar inte innebörden av effect_count: endast produktförflyttningar räknas. Arbetsområde och konservativ geometrisk kollisionskontroll är egna simulatorregler, inte certifierad robotbanplanering. Små källpositionsfel kan centreras inom en uttrycklig syntetisk grepptolerans; det är ingen modell av riktiga gripkrafter eller uppmätt robotnoggrannhet.

### 2.3 PLC, beräkning och drift

| Aspekt | Verklighetsanknytning | Vad demonstratorn inte styrker |
|---|---|---|
| PLC | Finns i rollens integrationsområde. [S01] | Att ett logiskt signalobjekt är ett testat PLC-program. |
| OPC UA | Har informationsmodell och kommunikationstjänster. [S18] | Att ett JSON-API innebär OPC UA-stöd. |
| GPU | LUMI-arbete och DGX-leverans är offentliggjorda. [S10][S11] | Att simulatorn motsvarar träning på B200. |
| Drift | Rollen omfattar system i kundmiljö. [S01] | Tillgänglighet över månader, jourförmåga eller verkligt serviceansvar. |
| Säkerhet | Verklig utrustning har egna säkerhetskrav och risker. | Funktionell säkerhet, validerat nödstopp eller CE-underlag. |

## 3. Vilken typ av realism är viktig?

### 3.1 Semantisk realism

Projektets viktigaste mål är att betydelsen i meddelandena ska vara konsekvent. Kundens begäran, integrationens avsikt och robotens exekveringsförsök ska inte ha samma otydliga ”klart”-flagga. Begrepp som accepterat, utfört, verifierat och kundkvitterat måste kunna skiljas åt.

Detta går att demonstrera med enkla objekt och låg grafisk detaljnivå. En grå låda som hamnar i fel destination är ett bättre testfall än en fotorealistisk kartong vars position aldrig kontrolleras.

### 3.2 Beteendemässig realism

Systemet ska kunna visa plausibla felreaktioner: en tjänst förlorar svaret, ett objekt är skymt, en kvittens återlevereras och en gammal plan når en återställd scen. Reaktionerna måste följa definierade regler, inte en demonstration som är skriptad för att alltid lyckas.

Vi modellerar dock inte hela felpopulationen i en riktig anläggning. Inga slutsatser om sannolikheten för driftstopp kan dras från att ett antal utvalda fel har hanterats.

### 3.3 Fysikalisk och perceptuell realism

Fysikalisk realism är låg i första versionen. Simulatorn kan kontrollera geometriska villkor men saknar exempelvis verklig kontaktfysik, deformation och materialvariation. Perceptuell realism är också begränsad om objektens identiteter kommer från metadata.

HKM-inspirationen ändrar inte detta. Inga proprietära CAD-filer, verkliga styrparametrar eller annonserade cykeltider används för att legitimera vår visuella rörelse. Om artikulerad dynamik, IK eller sensorbaserad rörelseplanering blir ett faktiskt krav behöver verktygsvalet omprövas; officiell PyBullet- och Isaac Sim-dokumentation beskriver sådana funktioner. De är jämförelsekällor, inte installerade simulatorberoenden. [S28][S29][S30]

En valfri bildmodell höjer inte automatiskt realismen till produktionsnivå. Bilder från Blender kan avvika systematiskt från verkliga kamerabilder. Dessutom kan modellens klassificering vara korrekt samtidigt som koordinater eller tidpunkter är fel.

### 3.4 Operationell realism

Loggning, idempotens och återhämtning kan vara ganska realistiska trots en enkel värld. Däremot saknas människor som flyttar gods, underhållspersonal, skiftbyten, leverantörsgränser, nätverkssegment och verkliga incidentprocesser. Dessa ska inte döljas bakom ett dashboard-uttryck som ”production ready”.

## 4. ”Digital twin” är ett projektnamn, inte en valideringsstämpel

RobotOps Twin ska i första hand beskrivas som en **simulerad cell med digital-tvilling-inspirerad systemdesign**. Vi saknar en verklig referenscell, en mätkedja som synkroniserar den och en utvärdering av modellens avvikelse från verkligheten.

Axels examensarbetstitel ger en relevant tematisk koppling, men denna rapport har inte verifierat hela examensarbetets metod eller resultat. Det vore därför fel att säga att vår efterhandsverifiering i Blender är samma metod eller att en KTH-studie har validerat vår design. [S04]

Ett framtida digitalt tvillingarbete behöver definiera vilken tillgång som avbildas, vilka tillstånd som uppdateras, hur ofta uppdatering sker och vilka avvikelser som accepteras för den avsedda användningen. Det räcker inte att två skärmar visar samma robotform.

## 5. Den viktigaste gränsen: kontroll av kommando kontra kontroll av effekt

### 5.1 Vad som faktiskt kan testas

Inom vår modell kan test-oraklet räkna hur många gånger ett objekt har flyttats och om affärsstatus motsvarar slutläget. Därmed går det att upptäcka logiska fel: samma order skapar två effekter, gamla kommandon körs efter scenreset eller en kundkvittens orsakar ett nytt robotplock.

Den ordinarie verifieraren ska däremot arbeta med begränsad observation. Att test-oraklet vet exakt var objektet finns betyder inte att driftlogiken har samma kunskap.

### 5.2 Vad som inte kan bevisas

Ett lyckat test visar inte att en fysisk robot aldrig dubbelplockar. Ett plock kan misslyckas på sätt som vår modell inte innehåller. Två funktioner kan dela samma felaktiga antagande och ändå vara överens.

Exempel: simulatorn flyttar ett objekt genom att ändra dess parent och verifieraren läser samma parent-fält. Då kan båda rapportera framgång utan att vi har testat en oberoende sensorväg. Därför ska test-orakel, observerad värld och beslut särskiljas, och kvarvarande gemensamma beroenden redovisas.

### 5.3 Oavgjort är ett legitimt resultat

Vid kvittensförlust kan journal och ny observation stödja ett slutförande. Men om journalen är borta och objektet skymt bör systemet inte gissa. En tydlig `REQUIRES_INTERVENTION` är i det fallet mer korrekt än att forcera flödet till grönt.

Demonstrationen ska visa både ett återhämtningsbart fel och ett ärligt oavgjort fall. Då blir det tydligt att reconciliation inte är en magisk funktion som alltid vet vad som hände.

## 6. Vad ett byte till verklig hårdvara skulle kräva

En adaptergräns är värdefull men ett hårdvarubyte är ett integrationsprojekt. Tabellen nedan beskriver ett föreslaget införandeförfarande, inte SICS AI:s process.

| Steg | Nödvändigt underlag | Föreslagen beslutsgrind |
|---|---|---|
| 1. Kontraktsgranskning | Leverantörens API, felkoder, enheter och kvittenser. | Alla kommandomappningar och okända fall dokumenterade. |
| 2. Risk- och ansvarsfördelning | Ansvariga för cell, robot, arbetsmiljö och säkerhetsfunktioner. | Ingen rörelse med oklart säkerhetsansvar. |
| 3. Geometri och kalibrering | Verkliga koordinatsystem, verktyg och tillåtna områden. | Mätningar och verifiering mot avsedd uppgift. |
| 4. Kontrollerat hårdvaruprov | Avgränsad testmiljö och godkända rutiner. | Rörelse, stopp och felrespons granskade av ansvariga. |
| 5. Affärssystemtest | Riktiga kundregler och representativa data. | Order- och inventeringssemantik accepterad av kund. |
| 6. Driftprov | Övervakning, återställning, versionsbyte och support. | Mätbara acceptanskriterier och kända begränsningar. |

Varken rapportpaketet eller simulatorns logik ska användas som säkerhetsinstruktion för fysisk utrustning. Funktionell säkerhet måste hanteras av personer med rätt ansvar och kompetens i den aktuella anläggningen.

## 7. Påståenden som är rimliga respektive missvisande

| Rimlig formulering | Missvisande formulering |
|---|---|
| ”Jag har specificerat en simulerad order–robot-kedja.” | ”Jag har byggt SICS system.” |
| ”Det här är ett test av idempotens inom en definierad felmodell.” | ”Det här garanterar exactly-once i den fysiska världen.” |
| ”Blender ersätter den fysiska cellen i demonstrationen.” | ”Modellen är en validerad tvilling av Nowastes cell.” |
| ”En deterministisk adapter föreslår handlingar.” | ”Jag har återskapat deras inlärda robotbrain.” |
| ”Stoppet är en logisk simulering.” | ”Systemet har ett certifierat nödstopp.” |
| ”Bildmodellen lämnar ett förslag som valideras.” | ”Schemakorrekt AI-utdata är säkert att exekvera.” |
| ”OPC UA är ett planerat tillägg.” | ”PLC/OPC UA är klart eftersom jag har en signalvy.” |
| ”Det här behöver testas på verklig hårdvara.” | ”Byt adapter så är allt produktionsklart.” |

Implementerade delar beskrivs som genomförda endast när de kan kopplas till sparad evidens. Valfria tillägg ska fortsatt märkas som framtida. Testresultat ska länka till en körning och en commit, inte bara till en skärmbild.

## 8. Vad som avsiktligt ligger utanför projektet

Den första versionen omfattar inte AGI-forskning, egen foundationmodell, full HKM1800-kinematik, säkerhets-PLC, komplex kontaktfysik, storskalig GPU-träning, flerrobotsamordning, verklig AutoStore-integration eller ett komplett ERP. Den omfattar inte heller säkerhetscertifiering, juridisk bedömning eller revision av SICS AI.

Detta är inte ett argument för att dessa områden är oviktiga. Avgränsningen gör i stället att de delar som faktiskt byggs kan förstås, testas och diskuteras. En liten design med uttryckliga begränsningar är lättare att granska än en bred demo som använder många tekniska namn utan motsvarande implementation.

GitHub Pages-publiceringen är en dokumentationsleverans. Den ska inte förväxlas med en molndriftsatt simulator. Python, lokal databas, Blender och eventuella modellnycklar hör till en separat körmiljö. [S19]

## 9. Risker, motåtgärder och kvarvarande osäkerhet

| Risk | Föreslagen motåtgärd | Kvarvarande begränsning |
|---|---|---|
| Visuell realism övertygar mer än tester. | Visa status och effektjournal tillsammans med grafiken. | Grafiken kan ändå ge ett starkare intryck än modellen motiverar. |
| Verifieraren läser facit. | Separera sensorväg och test-orakel. | Båda delar simulatorns grundantaganden. |
| För många verktyg försämrar leveransen. | En lokal cell och ett aktivt uppdrag. | Ingen skalbarhetsvalidering. |
| LLM gör demonstrationen instabil. | Deterministisk baslinje och tydlig felpolicy. | Baslinjen visar inte modellens intelligens. |
| Återställning raderar bevis. | Epoker, beständig historik och export av körning. | En inkonsistent fysiskliknande värld kan kräva granskning. |
| Agentverktyg får för stor behörighet. | Isolerat scenförfattande; inget MCP i runtime. | Utvecklingsmiljön behöver fortfarande skyddas. |

Blender Labs egen varning om exekvering av modellgenererad kod är motiv för separationen mellan författande och drift. Det är inte ett påstående om att ett visst MCP-paket har använts eller säkerhetsgranskats i denna version. [S12]

## 10. Slutsats och kontrollista för presentation

Den rimliga ambitionen är **hög tydlighet i integrationssemantik och låg, öppet deklarerad fysisk realism**. Projektet ska göra det möjligt att diskutera var beslut tas, vem som äger tillstånd och vad som händer när observation och journal inte stämmer överens.

Före varje demonstration ska projektägaren kunna besvara följande i vanliga ord: vad är implementerat, vad är simulerat, vilka källor inspirerade valet, vilka tester har körts och vad kräver fortfarande verklig utrustning? När dessa svar är tydliga blir begränsningarna en del av det tekniska resonemanget, inte något som behöver döljas.

**Rapportens slutsats är inte att simulatorn motsvarar den verkliga miljön. Slutsatsen är att den kan bevara utvalda, betydelsefulla integrationsproblem samtidigt som den gör deras gränser synliga.**
