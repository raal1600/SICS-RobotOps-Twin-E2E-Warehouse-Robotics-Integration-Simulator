import ast
import html
import re
from pathlib import Path

import pytest


@pytest.fixture
def publication_links(tmp_path):
    source = Path(__file__).resolve().parents[2] / "tools" / "build_publication.py"
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "validate_links"
    )
    site = tmp_path / "site"
    site.mkdir()
    namespace = {"OUT": site, "html": html, "re": re}
    # Execute the real validator without importing the unrelated PDF/rendering dependencies.
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"), namespace)
    return site, namespace["validate_links"]


@pytest.mark.parametrize("href", ["../docs/outside.md", "%2e%2e/docs/outside.md"])
def test_publication_rejects_existing_target_outside_site(publication_links, href):
    site, validate = publication_links
    outside = site.parent / "docs" / "outside.md"
    outside.parent.mkdir()
    outside.write_text("Existing repository document outside the served root.", encoding="utf-8")
    (site / "index.html").write_text(f'<a href="{href}">Document</a>', encoding="utf-8")

    with pytest.raises(ValueError, match="outside publication root"):
        validate()


def test_publication_accepts_local_download_fragment_and_external_links(publication_links):
    site, validate = publication_links
    (site / "downloads").mkdir()
    (site / "downloads" / "report.pdf").write_bytes(b"fixture download")
    (site / "page.html").write_text('<h1 id="section">Page</h1>', encoding="utf-8")
    (site / "index.html").write_text(
        '<main id="main"><a href="#main">Same page</a>'
        '<a href="page.html#section">Page section</a>'
        '<a href="downloads/report.pdf">Download</a>'
        '<a href="https://example.invalid/document">External</a></main>',
        encoding="utf-8",
    )

    validate()


@pytest.mark.parametrize(
    ("href", "message"),
    [("missing.html", "Broken link"), ("page.html#missing", "Missing fragment")],
)
def test_publication_retains_missing_target_and_fragment_rejection(
    publication_links, href, message
):
    site, validate = publication_links
    (site / "page.html").write_text('<h1 id="present">Page</h1>', encoding="utf-8")
    (site / "index.html").write_text(f'<a href="{href}">Target</a>', encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        validate()
