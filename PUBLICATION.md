# Publicerings- och underhållsguide

Detta repository innehåller en **deterministisk simulator, ett rapportpaket och en byggkedja för dokumentation**. Implementationsstatus finns i GOAL_PROGRESS.md och publication/status.json; lokal och fjärrverifierad acceptans redovisas i ACCEPTANCE_REPORT.md.

## Innehåll och redigering

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
Källornas kontrolltid är 1 oktober 2026; implementationsrevisionen är 1.1 från
2 oktober 2026. De datumen avser olika saker.

## Utdata

Bygget skapar sju HTML-sidor, inklusive aktuell governance/status, sju SVG-diagram, motsvarande Mermaid-definitioner, tre separata PDF-rapporter, ett samlat PDF-paket, Markdown-källor, BibTeX och JSON-register. `build.json` innehåller källcommit, sidantal och PDF-hashar.

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
Attention opens the original pick review; navigation never decides an outcome or
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

The guided-workspace release is verified for clean source `59ace31`: all MUST
criteria pass, and CI, Windows native lifecycle checks and public publication are
green. [Release provenance](docs/evidence/workspace-release.json) retains artifact
checksums and workflow URLs; the acceptance report names its audited source. The
evidence/status successor is checked again by CI and Pages, whose artifacts and
public build.json record that final SHA (ADR 0002). Earlier local-only notes are
historical and do not restrict the now-authorized publication.
