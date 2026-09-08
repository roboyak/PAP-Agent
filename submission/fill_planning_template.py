#!/usr/bin/env python3
"""Fill the supplied six-page template, preserving its interactive answer fields.

Requires pypdf and reportlab. Edit planning_template_content.json, then run with a new --output
path. Source templates and previous versions are never overwritten.
"""

import argparse
import json
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    RectangleObject,
    TextStringObject,
)
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
FONT_SIZE = 11
LEADING = 13.5
PADDING = 9


def field_name(widget):
    return widget.get("/T") or widget["/Parent"].get_object()["/T"]


def appearance(writer, widget, value):
    """Build a wrapped, padded appearance; reject overflow instead of hiding text."""
    x0, y0, x1, y1 = map(float, widget["/Rect"])
    width, height = x1 - x0, y1 - y0
    lines = []
    for paragraph in value.split("\n"):
        line = ""
        for word in paragraph.split():
            if stringWidth(word, "Helvetica", FONT_SIZE) > width - 2 * PADDING:
                raise ValueError(f"Word too wide in {field_name(widget)}: {word}")
            candidate = f"{line} {word}".strip()
            if stringWidth(candidate, "Helvetica", FONT_SIZE) > width - 2 * PADDING:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    needed = FONT_SIZE + (len(lines) - 1) * LEADING + 3
    if needed > height - 2 * PADDING:
        raise ValueError(f"Answer too tall in {field_name(widget)}: shorten the text")
    assert " ".join(" ".join(lines).split()) == " ".join(value.split())
    buffer = BytesIO()
    drawing = canvas.Canvas(buffer, pagesize=(width, height))
    text = drawing.beginText(PADDING, height - PADDING - FONT_SIZE)
    text.setFont("Helvetica", FONT_SIZE)
    text.setLeading(LEADING)
    for line in lines:
        text.textLine(line)
    drawing.drawText(text)
    drawing.save()
    page = PdfReader(buffer).pages[0]
    stream = DecodedStreamObject()
    stream.set_data(page.get_contents().get_data())
    stream.update(
        {
            NameObject("/Type"): NameObject("/XObject"),
            NameObject("/Subtype"): NameObject("/Form"),
            NameObject("/BBox"): RectangleObject([0, 0, width, height]),
            NameObject("/Resources"): page["/Resources"].clone(writer),
        }
    )
    return DictionaryObject({NameObject("/N"): writer._add_object(stream)})


def verify(pdf, answers):
    reader = PdfReader(pdf)
    assert len(reader.pages) == 6, "Expected the original six-page template"
    fields = reader.get_fields()
    assert set(fields) == set(answers), "The template's ten answer fields must survive"
    for name, value in answers.items():
        assert fields[name]["/V"] == value, f"Canonical value mismatch: {name}"
    seen = set()
    for page in reader.pages:
        for ref in page.get("/Annots", []):
            widget = ref.get_object()
            if widget.get("/Subtype") != "/Widget":
                continue
            name = field_name(widget)
            parent = widget.get("/Parent", ref).get_object()
            assert widget.get("/V", parent.get("/V")) == answers[name], name
            assert widget["/AP"]["/N"].get_object().get_data(), name
            seen.add(name)
    assert seen == set(answers), "Missing answer widgets"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--template", type=Path, default=HERE / "7.1_Capstone_Planning_Template.pdf"
    )
    parser.add_argument("--content", type=Path, default=HERE / "planning_template_content.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() == args.template.resolve() or args.output.exists():
        parser.error("Choose a new output filename; existing PDFs are preserved")
    content = json.loads(args.content.read_text())
    answers = content["answers"]
    assert set(answers) == {f"Answer{i}" for i in range(1, 11)}
    assert all(value.strip() and value.isascii() for value in answers.values())
    writer = PdfWriter()
    writer.clone_document_from_reader(PdfReader(args.template))
    assert set(writer.get_fields()) == set(answers), "Unexpected form; inspect before filling"
    # Answer1/2 have parent fields plus child widgets with their own empty /V.
    # Fill both representations so viewers cannot show a stale child value.
    for page in writer.pages:
        for ref in page.get("/Annots", []):
            widget = ref.get_object()
            if widget.get("/Subtype") == "/Widget":
                widget[NameObject("/V")] = TextStringObject(answers[field_name(widget)])
    writer.update_page_form_field_values(None, answers, auto_regenerate=False, flatten=False)
    # pypdf's generated appearances honor explicit newlines but do not word-wrap.
    # Replace just their appearance streams, retaining the complete editable values.
    for page in writer.pages:
        for ref in page.get("/Annots", []):
            widget = ref.get_object()
            if widget.get("/Subtype") == "/Widget":
                widget[NameObject("/AP")] = appearance(writer, widget, answers[field_name(widget)])
                widget[NameObject("/DA")] = TextStringObject("/Helv 11 Tf 0 g")
                if "/Parent" in widget:
                    widget["/Parent"][NameObject("/DA")] = TextStringObject("/Helv 11 Tf 0 g")
    writer.add_metadata(
        {
            "/Title": content["title"],
            "/Author": content["author"],
            "/Subject": f"Completed {content['date']}; implementation {content['evidence_commit']}",
        }
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        writer.write(stream)
    verify(args.output, answers)
    words = sum(len(value.split()) for value in answers.values())
    print(f"Created {args.output}: 6 pages, 10 editable answers, {words} words.")
    print("Field values and appearance streams verified. Render all pages for visual review.")


if __name__ == "__main__":
    main()
