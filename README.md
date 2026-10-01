# RobotOps Twin

### End-to-End Warehouse Robotics Integration Simulator — forsknings- och designunderlag

**[Öppna rapportpaketet på GitHub Pages](https://raal1600.github.io/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/)**

[![Build and publish research reports](https://github.com/raal1600/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/actions/workflows/publish-reports.yml/badge.svg)](https://github.com/raal1600/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/actions/workflows/publish-reports.yml)

Ett oberoende, svenskt rapportpaket om hur kundens lagerorder kan kopplas till AI-assisterad robotexekvering, verifiering och återhämtning. Blender är den **planerade simulatorvärlden**, inte en validerad kopia av en verklig anläggning.

**Aktuell status:** rapporter, diagram och publiceringskedja finns. Den fullständiga ERP/robot-simulatorn är specificerad men ännu inte implementerad eller empiriskt validerad i detta repository. Projektet är inte beställt eller godkänt av SICS AI.

## Läs och ladda ned

| Rapport | Webb | PDF |
|---|---|---|
| 01. Från kundorder till verifierad roboteffekt | [Designstudie](https://raal1600.github.io/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/design.html) | [Ladda ned](https://raal1600.github.io/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/downloads/01-design.pdf) |
| 02. Simulatorn och den verkliga robotcellen | [Avgränsning](https://raal1600.github.io/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/avgransning.html) | [Ladda ned](https://raal1600.github.io/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/downloads/02-avgransning.pdf) |
| 03. Teknisk dialog om RobotOps Twin | [Diskussionsunderlag](https://raal1600.github.io/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/diskussion.html) | [Ladda ned](https://raal1600.github.io/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/downloads/03-diskussion.pdf) |

**[Alla tre rapporterna i en PDF](https://raal1600.github.io/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/downloads/robotops-twin-samlat.pdf)** · [Diagramgalleri](https://raal1600.github.io/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/diagram.html) · [Källregister](https://raal1600.github.io/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/kallor.html)

PDF-filer och färdig webbplats finns också i den genererade [gh-pages-grenen](https://github.com/raal1600/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/tree/gh-pages). Publiceringshistorik och HTTP-kontroller finns i Actions.

## Konceptet

```mermaid
flowchart LR
    ERP[ERP / WMS] --> INT[Pythonintegration]
    INT --> PLAN[Observation och planförslag]
    PLAN --> VALID[Validering och celltillåtelse]
    VALID --> ROBOT[RobotGateway]
    ROBOT --> BLENDER[Blender-värld]
    BLENDER --> VERIFY[Observation och verifiering]
    VERIFY --> SYNC[Kundkvittens]
    SYNC --> ERP
```

Huvudfallet är ett plock som genomförs medan kvittensen försvinner. Systemet ska då inte anta att handlingen uteblev. Det ska markera okänt utfall och stämma av journal och observation utan ett omotiverat nytt plock. Otillräcklig evidens ska kunna leda till granskning i stället för ett falskt grönt resultat.

## Underlag och avgränsning

Rapporterna skiljer offentliga uppgifter, självrapporterade företagsresultat, egna designbeslut och kunskapsluckor. Inspirationen kommer bland annat från CloudGripper/AutoGrasper, R900, SICS AI:s offentliga roll- och HYPER-material samt Cognibotics installationsbeskrivning. Källorna är spårbara; ingen proprietär robotbrain eller AGI-implementation påstås vara återskapad.

Sju originaldiagram kan redigeras som Mermaid eller via JSON-layouten. Källkod och text är AI-assisterade. Rapportpaketet är inte sakkunniggranskat. Inga privata rekryteringsmeddelanden eller interna företagsdokument publiceras.

## Bygg dokumentationen lokalt

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-docs.txt
python tools/build_publication.py
python -m http.server 8000 --directory _site
```

Python 3.13 och Pango/DejaVu behövs. Se [PUBLICATION.md](PUBLICATION.md) för systemberoenden, publicering och visuell kvalitetskontroll. GitHub Pages kör enbart dokumentationen, inte Blender eller Pythonbackend.

## Struktur

```text
reports/                 Tre redigerbara Markdown-rapporter
publication/             Källregister, diagramlayout och CSS
 tools/build_publication.py   HTML-, SVG-, Mermaid- och PDF-bygge
.github/workflows/       Bygge, publicering och HTTP-kontroll
CITATION.cff             Citeringsmetadata
PUBLICATION.md           Underhålls- och publiceringsguide
```

Rami Halabi · Version 1.0 · 1 oktober 2026. Befintlig [MIT-licens](LICENSE) behålls. Länkade källor och varumärken tillhör respektive rättighetsinnehavare.
