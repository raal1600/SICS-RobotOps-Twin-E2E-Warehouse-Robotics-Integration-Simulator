# Publicerings- och underhållsguide

Detta repository innehåller ett **rapportpaket och en byggkedja för dokumentation**. Implementationsstatus finns i GOAL_PROGRESS.md och publication/status.json; fullständig runtime-acceptans återstår.

## Innehåll och redigering

Redigera rapporterna i `reports/`. Referenser ligger i `publication/references.json`. Diagrammens texter, noder och positioner ligger i `publication/diagrams.json`. `tools/build_publication.py` genererar både SVG och redigerbar Mermaid från samma diagramdefinitioner. Mermaid beskriver den logiska strukturen; JSON styr layouten för publicerade SVG-bilder.

Källmarkörer som `[S03]` länkas automatiskt till en fullständig källförteckning i respektive rapport. Nya sakuppgifter ska ha en identifierbar källa och ett tydligt bevisvärde. Uppdatera datum/version vid en materiell revision. Skriv inte om planerade tester till genomförda resultat utan körningsdata.

## Lokal byggning

Använd Python 3.13 och en miljö med Pango, Fontconfig och DejaVu installerade. Exempel för Ubuntu:

```bash
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 fonts-dejavu-core
python3 -m venv .venv
source .venv/bin/activate
python -m pip install uv==0.12.13
uv sync --locked --all-groups
uv run --locked python -m tools.dev docs
python -m http.server 8000 --directory _site
```

Öppna `http://localhost:8000`. Bygget skriver endast i `_site/`. Lägg inte egen källkod eller manuella original där, eftersom katalogen återskapas. Systemtypsnitt används vid PDF-framställning, men inga typsnittsfiler distribueras i repositoryt.

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
