from pypdf import PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, FloatObject, NameObject, TextStringObject

from tools.pdf_package import merge_reports


def test_pdf_package_preserves_colliding_report_section_names(tmp_path):
    inputs = []
    for i in range(2):
        writer = PdfWriter()
        writer.add_blank_page(width=300, height=300)
        writer.add_named_destination("section-1", 0)
        writer.add_annotation(
            0,
            DictionaryObject(
                {
                    NameObject("/Type"): NameObject("/Annot"),
                    NameObject("/Subtype"): NameObject("/Link"),
                    NameObject("/Rect"): ArrayObject([FloatObject(n) for n in (10, 10, 40, 40)]),
                    NameObject("/Dest"): TextStringObject("section-1"),
                }
            ),
        )
        path = tmp_path / f"report-{i}.pdf"
        writer.write(path)
        inputs.append((path, f"Report {i}"))
    result = merge_reports(inputs, tmp_path / "combined.pdf")
    assert result == {"pages": 2, "internal_links_checked": 2, "destinations_preserved": True}
