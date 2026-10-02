"""Merge reports without cross-report collisions in named section destinations."""

from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, NameObject


def merge_reports(inputs: list[tuple[Path, str]], output: Path) -> dict:
    writer = PdfWriter()
    expected = []
    offset = 0
    for path, title in inputs:
        reader = PdfReader(path)
        for page in reader.pages:
            for annotation in page.get("/Annots", []):
                link = annotation.get_object()
                owner, key = link, "/Dest"
                if "/A" in link and link["/A"].get("/S") == "/GoTo":
                    owner, key = link["/A"], "/D"
                destination = owner.get(key)
                if isinstance(destination, str):
                    resolved = reader.named_destinations[destination]
                    owner[NameObject(key)] = ArrayObject(resolved.dest_array)
                    expected.append(offset + reader.get_destination_page_number(resolved))
                elif isinstance(destination, list):
                    expected.append(offset + reader.get_page_number(destination[0].get_object()))
        writer.append(reader, outline_item=title)
        offset += len(reader.pages)
    writer.add_metadata({"/Title": "RobotOps Twin - collected reports", "/Author": "Rami Halabi"})
    with output.open("wb") as file:
        writer.write(file)
    combined = PdfReader(output)
    page_ids = {page.indirect_reference.idnum: i for i, page in enumerate(combined.pages)}
    actual = []
    for page in combined.pages:
        for annotation in page.get("/Annots", []):
            link = annotation.get_object()
            destination = link.get("/Dest")
            if "/A" in link and link["/A"].get("/S") == "/GoTo":
                destination = link["/A"].get("/D")
            if destination is not None:
                if not isinstance(destination, list):
                    raise ValueError("Unresolved merged PDF destination")
                actual.append(page_ids[destination[0].idnum])
    if actual != expected or len(combined.pages) != offset:
        raise ValueError("Merged PDF lost or redirected an internal link")
    return {"pages": offset, "internal_links_checked": len(actual), "destinations_preserved": True}
