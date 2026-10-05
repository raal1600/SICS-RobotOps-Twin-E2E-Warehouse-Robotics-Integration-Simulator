# Publicerings- och underhållsguide

Detta repository innehåller en **deterministisk simulator, ett rapportpaket och en byggkedja för dokumentation**. Implementationsstatus finns i GOAL_PROGRESS.md och publication/status.json; lokal och fjärrverifierad acceptans redovisas i ACCEPTANCE_REPORT.md.

## Innehåll och redigering

### Final lifecycle/runtime verification (2026-10-05)

The final-source replay-read/delete race and local Blender deadlines remain
archived with their original failures. Client response draining and process-local
Windows Blender QoS now have targeted browser, runtime and contract evidence.
Source S31 adds official Blender command-line documentation; previous research
classifications remain unchanged. Runtime/plan/handoff/playback sources and the
design report describe the same bounded invocation. Architecture and state
boundaries are unchanged. New complete acceptance and final-source publication
verification remain required; the accepted revisions below retain their own scope.

### Delete versus clear correction (2026-10-05)

ADR 0013 implements the owner's updated lifecycle semantics: delete purges the
test entry/world and releases its number; clear keeps that test for a fresh run.
Pending cleanup/reset and anonymous request digests preserve safe retries.
The df45c93 implementation passes all 118 MUSTs with 688 tests twice, 91.66%
coverage and successful exact-source CI/native/publication workflows.
[Evidence and mapping correction](docs/evidence/test-reset-final/README.md) remain
separate from accepted historical revisions below. API/contracts, operator guides,
all three reports, architecture caption and citation version 1.4 are synchronized.
The generated Pages/PDFs are rebuilt through the normal process; the final
evidence/status successor gets its own complete CI and deployed-SHA verification.
External source entries and provenance classifications are unchanged.

### Accepted investigation workflow revision (2026-10-05)

Clean source `7b9f0a656cdd077106ab4b7ee7ade82335e11f26` passes all 118 MUSTs.
[The refreshed report evidence](docs/evidence/acceptance/20261005T014537/manifest.json)
and [CI/browser/publication archive](docs/evidence/investigation-ui-final/README.md)
retain repeated suites, source hashes, screenshots, eight Blender demos and
published source/link/PDF checks. The first stale-label failure remains archived.
Publication 1.3 / 2026-10-05 synchronizes the new investigation diagram, operator
flow and status across sources. The 30 research entries keep their earlier control
dates and provenance categories; this UI work adds no manufacturer-performance claim.
Every evidence/status successor is checked again by complete CI and the deployed
build SHA. Earlier acceptance is never relabelled to cover a later commit.

### Cell-selection and test-data lifecycle revision (2026-10-04)

ADR 0011 adds one currently selectable HKM cell and explicit test-data retention
controls. Synchronize their API/UI descriptions and architecture diagram before
rebuilding. Current verification status belongs to GOAL_PROGRESS.md,
ACCEPTANCE_REPORT.md and the generated shared status block; do not infer a new
PASS from the earlier accepted HKM publication.

The lifecycle revision is accepted for clean source
`b1c374ae76144309cc4476392dec681292f0e3a7`: all 110 MUSTs pass in the
[refreshed acceptance manifest](docs/evidence/acceptance/20261004T204452/manifest.json).
[The exact-source remote archive](docs/evidence/test-management-final/README.md)
preserves successful CI/desktop/publication workflows, public build attribution,
PDF hashes and link/layout checks. Its original public status predates completed
acceptance and is retained unchanged. Rebuild synchronized status sources and
verify the final evidence/status successor's own CI and deployed SHA (ADR 0002).

### Historical HKM-inspired accepted revision (2026-10-04)

The HKM-inspired adaptation was accepted at audited source `ca779879`, with
publication successor `ae6d5d8`; its 110-MUST results retain that exact attribution.
The verified 59ace31 deterministic-system release remains
historical evidence. Exact prior and fresh eaf35b4 baseline reports are archived with hashes
in [baseline provenance](docs/evidence/hkm-baseline-eaf35b4/provenance.json).
The fresh baseline retains its repeated obsolete UI-label failure; no historical
report was rewritten to make the enhancement appear accepted.

Generate final geometry/frame/tool/state diagrams and product/tool compatibility
documentation from synchronized source/catalogue definitions. Report status
dates use current UTC. Preserve manufacturer/deployment claims separately from
our synthetic catalogue, visual kinematics, timing and collision rules. Rebuild
Pages/PDFs through the normal workflow after the coherent milestone, then verify
the actual deployed source SHA and public artifacts. A local build does not
establish remote publication or completed HKM requirements.

Redigera rapporterna i `reports/`. Referenser ligger i `publication/references.json`. Diagrammens texter, noder och positioner ligger i `publication/diagrams.json`. `tools/build_publication.py` genererar både SVG och redigerbar Mermaid från samma diagramdefinitioner. Mermaid beskriver den logiska strukturen; JSON styr layouten för publicerade SVG-bilder.

Källmarkörer som `[S03]` länkas automatiskt till en fullständig källförteckning i respektive rapport. Nya sakuppgifter ska ha en identifierbar källa och ett tydligt bevisvärde. Uppdatera datum/version vid en materiell revision. Skriv inte om planerade tester till genomförda resultat utan körningsdata.

## Lokal byggning

Använd Python 3.13 och en miljö med Pango, Fontconfig och DejaVu installerade. Exempel för Ubuntu:

```bash
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-dejavu-core
uv sync --locked --all-groups
uv run --locked python -m tools.dev docs
python -m http.server 8000 --directory _site
```

Öppna `http://localhost:8000`. Bygget skriver endast i `_site/`. Lägg inte egen källkod eller manuella original där, eftersom katalogen återskapas. Systemtypsnitt används vid PDF-framställning, men inga typsnittsfiler distribueras i repositoryt.

## Windows och PDF-bibliotek

Runtime/testkommandona fungerar även i PowerShell. PDF-bygget behöver Pango,
Fontconfig och typsnitt utöver de låsta Pythonpaketen. Följ
[WeasyPrints officiella Windows-anvisning](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows)
för MSYS2/Pango och sätt `WEASYPRINT_DLL_DIRECTORIES` till bibliotekskatalogen.
Den lokala verifieringen använde en isolerad conda-forge-miljö med Pango 1.58.2,
Cairo 1.18.6, Fontconfig 2.18.3 och Poppler 26.09.0. Den miljön är byggverktyg,
inte ett runtime- eller GPU-beroende. Exempel efter installation av bibliotek:

```powershell
$env:WEASYPRINT_DLL_DIRECTORIES = 'C:\path\to\pdf-env\Library\bin'
$env:PATH = $env:WEASYPRINT_DLL_DIRECTORIES + ';' + $env:PATH
uv sync --locked --all-groups
uv run --locked python -m tools.dev docs
```

CI använder Ubuntu-paketen ovan. PDF-sidantal kan skilja mellan plattformarnas
typsnittsversioner; manifestet redovisar det verkliga sidantalet och filhasharna.
Basgranskningen av källor gjordes 1 oktober 2026; HKM-kompletteringen granskades
4 oktober. Varje registerpost behåller sitt eget kontrolldatum och sin
proveniensklass. Publikationsrevisionen är 1.4 från 5 oktober 2026; implementationens
verifiering och aktuell acceptans visas separat i den gemensamma statusrutan.

## Utdata

Bygget skapar sju HTML-sidor, inklusive aktuell governance/status, SVG-diagram med motsvarande Mermaid-definitioner, tre separata PDF-rapporter, ett samlat PDF-paket, Markdown-källor, BibTeX och JSON-register. Antal diagram och källor hämtas ur aktuella register. `build.json` innehåller källcommit, sidantal, källornas kontrolldatum och PDF-hashar.

Produkt-/verktygstabellen och dess Mermaid-källa genereras från
`robotops/robotics/catalogue-v1.json` via `python -m tools.generate_robotics_docs`.
`make docs` kör samma generator före publiceringsbygget; `--check` upptäcker
drift utan att skriva filer. Diagrammet `product-tool-compatibility` använder
samma katalog vid SVG-rendering. Redigera katalogen och generera om, inte
`docs/generated/product-tool-catalogue.md` eller den genererade Mermaid-filen
för hand. Katalogens existens är inte evidens för godkänd körning.

Automatiska kontroller fångar okända käll-ID:n, kvarvarande figurplatshållare, ogiltig SVG-XML, bristande PDF-textutvinning samt trasiga interna länkar/ankare. Dessa kontroller ersätter inte visuell PDF- och webbläsargranskning.

## GitHub Actions och Pages

Workflowen `.github/workflows/publish-reports.yml` bygger på ändringar i dokumentationskällorna och kan också startas manuellt. Den arkiverar hela webbplatsen som `robotops-publication` och sparar genererade filer i grenen `gh-pages`. Detta gör PDF-filerna tillgängliga även om Pages första aktivering kräver administrativ inställning.

Publikationsadress:

https://raal1600.github.io/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/

Första aktiveringen, när Pages ännu inte är aktiverat: öppna repositoryts **Settings → Pages**, välj **GitHub Actions** som källa och kör workflowen igen. Den vanliga `GITHUB_TOKEN` som används av byggjobbet ersätter inte alla administrativa inställningar. Inga personliga åtkomsttoken eller API-nycklar ska läggas i repositoryt.

En alternativ publiceringskälla är grenen `gh-pages` och katalogen `/ (root)`. Välj en publiceringsmetod konsekvent; den medföljande deploy-jobben använder GitHub Actions. Kopiera inte simulatorhemligheter till den publika dokumentationsgrenen.

## Manuell kvalitetskontroll

Kontrollera omslag, innehållsförteckning, tabeller, kodblock, samtliga figurer och källförteckningar i varje PDF. Kontrollera att diagrammens text är läsbar och att inga element överlappar. Testa webbplatsen på både en bred och en smal skärm samt att PDF-länkarna faktiskt laddar ned PDF-filer. Kontrollera den publicerade URL:en innan status ändras till publicerad.

## Licens och offentlighet

Repositoryts befintliga MIT-licens behålls. Egna rapporter och illustrationer omfattas av den, medan länkade källor och varumärken tillhör respektive rättighetsinnehavare. Inga tredje parts originalfigurer har kopierats. Inget samarbete eller godkännande från SICS AI, KTH, Cognibotics eller övriga källägare antyds.

Publicera inte anteckningar från ett framtida tekniskt möte eller nya interna uppgifter utan att först klargöra vad som får delas. Rapporternas diskussionsprotokoll är avsiktligt tomt.

The operations viewer vendors Three.js 0.180.0 under its upstream MIT license,
retained in apps/erp_ui/vendor/LICENSE. This software dependency is separate from
the publication's original figures. The scenario model remains SIMULATOR_DESIGN.

The independent-test extension (ADR 0007) is also SIMULATOR_DESIGN. Local builds
include the general test lifecycle, isolated storage and preserved read-only
history. These changes were initially retained locally at the user's request.
The user has now authorized release of the complete workspace update. CI and the
publication workflow must verify the exact committed source; the earlier local
builds alone do not establish a public deployment or remote acceptance.

ADR 0008 adds explicit re-observation after intervention within the same active
test. The state and reconciliation diagrams include the evidence-only return
path; old ambiguous assessments remain inspectable. This is SIMULATOR_DESIGN,
not a new external research finding or a guarantee of successful recovery.

ADR 0009 adds a dark operator workspace with a persisted-state next-step guide,
scenario expectations and readable evidence beside explicit re-observation.
The historical ADR 0009 attention behavior opened the original pick review; navigation never decides an outcome or
sends a command. The architecture caption, operational guides and current-status
sources describe this presentation boundary. Generated output still comes only
from the publication builder; local rebuilding does not publish these changes.

The selector-help follow-up adds definitions, affected stages and key differences
for every execution scenario and observation mode, with in-app comparison tables.
The [scenario guide](docs/implementation/scenarios.md) explains the different
injection times and similar-looking outcomes. It changes presentation only;
state, architecture, contracts and external source claims remain unchanged.
The earlier full-system acceptance remains a dated baseline; the separate UI
follow-up evidence records its own affected-suite and browser checks.

ADR 0012 supersedes automatic review opening with a highlighted investigation
action beside the cell. Its bounded panel separates symptoms, confirmed records
and possible explanations, exposes exact evidence and manual inspection paths,
and keeps the event timeline secondary. Opening it pauses only replay; return
preserves context. Reports and architecture captions describe this UI boundary,
not a new sensor, verifier or real-world research claim. Eight additive UI-INV
MUSTs require actual browser journeys and fresh acceptance of the changed source.
Screenshots/results remain revision-scoped; generated Pages/PDFs still come only
from the publication workflow. Functional automation is not a first-time user study.

The guided-workspace release is verified for clean source `59ace31`: all MUST
criteria pass, and CI, Windows native lifecycle checks and public publication are
green. [Release provenance](docs/evidence/workspace-release.json) retains artifact
checksums and workflow URLs; the acceptance report names its audited source. The
evidence/status successor is checked again by CI and Pages, whose artifacts and
public build.json record that final SHA (ADR 0002). Earlier local-only notes are
historical and do not restrict the now-authorized publication.
