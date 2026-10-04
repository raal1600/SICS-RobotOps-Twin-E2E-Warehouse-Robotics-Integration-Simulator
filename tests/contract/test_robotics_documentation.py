import json
from pathlib import Path

from tools.generate_robotics_docs import CATALOGUE, DOCUMENT, MERMAID, generate


def test_canonical_catalogue_documentation_detects_changed_compatibility(tmp_path):
    source = Path(CATALOGUE).read_text(encoding="utf-8")
    target = tmp_path / CATALOGUE
    target.parent.mkdir(parents=True)
    target.write_text(source, encoding="utf-8")
    assert set(generate(tmp_path, check=True)) == {DOCUMENT, MERMAID}
    generate(tmp_path)
    assert generate(tmp_path, check=True) == []
    table = (tmp_path / DOCUMENT).read_text()
    mermaid = (tmp_path / MERMAID).read_text()
    assert "SKU-A / small carton | P | C | C | C | C | C" in table
    assert "SKU-F / long carton | N | C | N | C | N | P" in mermaid
    data = json.loads(source)
    data["products"][0]["compatibility"]["EE_SUPPORT_FORK"] = "N"
    target.write_text(json.dumps(data))
    assert set(generate(tmp_path, check=True)) == {DOCUMENT, MERMAID}
    generate(tmp_path)
    assert "SKU-A / small carton | P | C | C | C | C | N" in (tmp_path / DOCUMENT).read_text()
    assert "SKU-A / small carton | P | C | C | C | C | N" in (tmp_path / MERMAID).read_text()


def test_checked_in_catalogue_documentation_matches_runtime_source():
    assert generate(check=True) == []
