"""Build the report, recording plan, and video-link document from content.json."""

import json
import os
import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

SOURCE = Path(os.environ["PAP_SUBMISSION_SRC"])
OUTPUT = Path(os.environ["PAP_SUBMISSION_OUT"])
raw = json.loads((SOURCE / "content.json").read_text())
values = {**raw["facts"], "repository": raw["repository"]}


def expand(item):
    if isinstance(item, str):
        return re.sub(r"\{\{(\w+)\}\}", lambda m: values[m[1]], item)
    if isinstance(item, list):
        return [expand(x) for x in item]
    if isinstance(item, dict):
        return {k: expand(v) for k, v in item.items()}
    return item


content = expand(raw)


def document(title):
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = Inches(0.65)
    section.left_margin = section.right_margin = Inches(0.8)
    for name in ["Normal", "Title", "Subtitle", "Heading 1", "Heading 2"]:
        style = doc.styles[name]
        style.font.name = "Arial"
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.size = Pt(10.5 if name == "Normal" else 14)
        style.paragraph_format.space_after = Pt(7)
    doc.styles["Normal"].paragraph_format.line_spacing = 1.12
    doc.styles["Title"].font.size = Pt(25)
    doc.styles["Title"].font.bold = True
    doc.styles["Title"].paragraph_format.space_after = Pt(12)
    doc.styles["Subtitle"].font.size = Pt(11)
    doc.styles["Subtitle"].font.italic = False
    for border in list(doc.styles.element.iter(qn("w:pBdr"))):
        border.getparent().remove(border)
    doc.styles["Heading 1"].font.size = Pt(13)
    doc.styles["Heading 1"].font.bold = True
    doc.styles["Heading 1"].paragraph_format.space_before = Pt(10)
    doc.styles["Heading 1"].paragraph_format.keep_with_next = True
    doc.core_properties.author = content["author"]
    doc.core_properties.title = title
    doc.core_properties.subject = content["assignment"]
    footer = section.footer.paragraphs[0]
    footer.alignment = 2
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)
    return doc


def link(paragraph, label, url):
    relationship = paragraph.part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    element = OxmlElement("w:hyperlink")
    element.set(qn("r:id"), relationship)
    run, props = OxmlElement("w:r"), OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "174B70")
    props.append(color)
    run.append(props)
    text = OxmlElement("w:t")
    text.text = label
    run.append(text)
    element.append(run)
    paragraph._p.append(element)


def table(doc, headers, rows, widths):
    result = doc.add_table(rows=1, cols=len(headers))
    result.alignment = WD_TABLE_ALIGNMENT.CENTER
    result.autofit = False
    for column, width in zip(result.columns, widths, strict=True):
        column.width = Inches(width)
    for index, row_values in enumerate([headers, *rows]):
        row = result.rows[0] if index == 0 else result.add_row()
        tr_pr = row._tr.get_or_add_trPr()
        if index == 0:
            tr_pr.append(OxmlElement("w:tblHeader"))
        tr_pr.append(OxmlElement("w:cantSplit"))
        for cell, value, width in zip(row.cells, row_values, widths, strict=True):
            cell.width = Inches(width)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cell.text = value
            tc_pr = cell._tc.get_or_add_tcPr()
            borders = OxmlElement("w:tcBorders")
            for side in ["top", "left", "bottom", "right"]:
                edge = OxmlElement("w:" + side)
                for key, val in {"val": "single", "sz": "4", "color": "D9D9D9"}.items():
                    edge.set(qn("w:" + key), val)
                borders.append(edge)
            tc_pr.append(borders)
            margins = OxmlElement("w:tcMar")
            for side in ["top", "left", "bottom", "right"]:
                edge = OxmlElement("w:" + side)
                edge.set(qn("w:w"), "90")
                edge.set(qn("w:type"), "dxa")
                margins.append(edge)
            tc_pr.append(margins)
            shading = OxmlElement("w:shd")
            shading.set(
                qn("w:fill"), "183C53" if index == 0 else ("F4F7F9" if index % 2 else "FFFFFF")
            )
            tc_pr.append(shading)
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.04
                for run in p.runs:
                    run.font.size = Pt(9.5)
                    run.bold = index == 0
                    run.font.color.rgb = RGBColor.from_string("FFFFFF" if index == 0 else "000000")
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return result


def paragraphs(doc, items):
    for item in items:
        p = doc.add_paragraph()
        if content["repository"] in item:
            before, after = item.split(content["repository"], 1)
            p.add_run(before)
            link(p, content["repository"], content["repository"])
            p.add_run(after)
        else:
            p.add_run(item)


def report():
    doc = document(content["project"])
    doc.add_paragraph("DragonWings Power Availability\nProfile Forecaster", "Title")
    doc.add_paragraph("Final Capstone Report Section B", "Subtitle")
    doc.add_paragraph(f"{content['author']}\n{content['program']}\n{content['date']}")
    doc.add_heading("Project summary", 1)
    doc.add_paragraph(content["report"]["summary"])
    for index, page in enumerate(content["report"]["pages"]):
        if index:
            doc.add_page_break()
        for section in page:
            doc.add_heading(section["heading"], 1)
            paragraphs(doc, section["paragraphs"])
            if "table" in section:
                t = section["table"]
                widths = [1.3, 5.6] if len(t["headers"]) == 2 else [1.3, 3.1, 2.5]
                table(doc, t["headers"], t["rows"], widths)
            paragraphs(doc, section.get("after", []))
    doc.add_heading("Evidence sources", 1)
    for source in content["sources"]:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        p.add_run(f"{source['id']}  ")
        url = f"{content['repository']}/blob/{content['evidence_commit']}/{source['path']}"
        link(p, source["label"], url)
        for run in p.runs:
            run.font.size = Pt(9)
    doc.save(OUTPUT / "DragonWings_Final_Report.docx")


def clock(seconds):
    return f"{seconds // 60}:{seconds % 60:02d}"


def recording_plan():
    doc = document("DragonWings Presentation Plan and Recording Script")
    doc.add_paragraph("DragonWings Presentation Plan\nand Recording Script", "Title")
    doc.add_paragraph(f"{content['author']}   {content['date']}")
    main_duration = clock(sum(s["seconds"] for s in content["slides"]))
    pitch_duration = clock(sum(s["seconds"] for s in content["pitch_slides"]))
    doc.add_paragraph(
        f"The main presentation is planned for {main_duration}. "
        f"The separate {len(content['pitch_slides'])}-slide elevator pitch is planned "
        f"for {pitch_duration}. Use the slide notes as a speaking guide and rehearse "
        "at a natural pace before recording."
    )
    elapsed, rows = 0, []
    for i, slide in enumerate(content["slides"], 1):
        end = elapsed + slide["seconds"]
        rows.append([str(i), f"{clock(elapsed)}–{clock(end)}", slide["title"].replace("\n", " ")])
        elapsed = end
    table(doc, ["Slide", "Time", "Presentation outline"], rows, [0.55, 1.15, 5.2])
    doc.add_heading("Recording and submission", 1)
    for text in [
        "Rehearse the complete slide show, including the repository reference. "
        "Aim for 8–10 minutes and keep the slide visuals visible throughout.",
        "Record the main presentation with your own narration using your preferred recording "
        "tool. Check the completed video for clear audio, readable slides, and correct playback.",
        "Upload the recording to an accessible sharing platform. Add its URL to video_url in "
        "submission/content.json and rebuild the video-link document. Check the link while "
        "signed out or in a private browser window.",
        "Make the GitHub repository public before submission, as planned. Check its README "
        "and synthetic replay instructions while signed out.",
        "Upload the final report and the video-link document to Canvas. Clearly label the "
        "separate 90-second recording as optional if you submit it.",
    ]:
        doc.add_paragraph(text)
    for i, slide in enumerate(content["slides"], 1):
        if i % 3 == 1:
            doc.add_page_break()
        doc.add_heading(f"Slide {i}  {slide['title'].replace(chr(10), ' ')}", 1)
        doc.add_paragraph(f"{slide['checkpoint']}   Planned time {slide['seconds']} seconds")
        doc.add_paragraph(slide["notes"])
        doc.add_paragraph("Evidence  " + ", ".join(slide["sources"]))
    doc.add_heading("Optional elevator pitch", 1)
    handoffs, elapsed = [], 0
    for slide in content["pitch_slides"][:-1]:
        elapsed += slide["seconds"]
        handoffs.append(clock(elapsed))
    doc.add_paragraph(
        f"The intended slide handoffs are {', '.join(handoffs)}. "
        "The slide content supports a large classroom audience without requiring a live demo."
    )
    for i, slide in enumerate(content["pitch_slides"], 1):
        doc.add_heading(f"Slide {i}  {slide['title'].replace(chr(10), ' ')}", 1)
        doc.add_paragraph(f"Planned time {slide['seconds']} seconds")
        doc.add_paragraph(slide["notes"])
    doc.save(OUTPUT / "DragonWings_Presentation_Plan_and_Script.docx")


def video_links():
    doc = document("DragonWings Capstone Video Links")
    doc.add_paragraph("DragonWings Capstone Video Links", "Title")
    doc.add_paragraph(f"{content['author']}\n{content['assignment']}\n{content['date']}")
    doc.add_heading("Required presentation video", 1)
    p = doc.add_paragraph()
    if content["video_url"]:
        link(p, content["video_url"], content["video_url"])
    else:
        p.add_run(
            "VIDEO LINK PENDING  Add the accessible 8–10 minute recording URL before submitting."
        ).bold = True
    doc.add_heading("Presentation summary", 1)
    doc.add_paragraph(content["video_summary"])
    doc.add_heading("Project repository", 1)
    link(doc.add_paragraph(), content["repository"], content["repository"])
    doc.add_heading("Optional elevator pitch", 1)
    p = doc.add_paragraph()
    if content["optional_pitch_url"]:
        link(p, content["optional_pitch_url"], content["optional_pitch_url"])
    else:
        p.add_run(
            "OPTIONAL VIDEO LINK PENDING  Add the separate 90-second recording URL "
            "if submitting the elevator pitch."
        )
    doc.save(OUTPUT / "DragonWings_Video_Link_Submission.docx")


def faculty_brief():
    doc = document("DragonWings Faculty Showcase Preparation")
    doc.styles["Normal"].paragraph_format.space_after = Pt(5)
    doc.styles["Normal"].paragraph_format.line_spacing = 1.04
    doc.styles["Heading 1"].paragraph_format.space_before = Pt(8)
    doc.styles["Heading 1"].paragraph_format.space_after = Pt(5)
    doc.add_paragraph("DragonWings Faculty\nShowcase Preparation", "Title")
    doc.add_paragraph(content["author"])
    doc.add_paragraph(
        "Use the three-slide pitch for the 90-second showcase. These practice questions "
        "prepare for feedback on design, models, tools, evaluation, safety, and scaling. "
        "They are rehearsal prompts, not a prediction of the professor's questions."
    )
    for page, items in enumerate(content["faculty_questions"]):
        if page:
            doc.add_page_break()
        for item in items:
            doc.add_heading(item["topic"], 1)
            p = doc.add_paragraph(item["question"])
            p.runs[0].bold = True
            doc.add_paragraph(item["answer"])
    doc.add_heading("Live demonstration backup", 1)
    doc.add_paragraph(
        "Keep the 90-second pitch self-contained. If invited to demonstrate, open the "
        "already-running console, use the synthetic replay profile, run PAP, and show "
        "Context plus Trace. Model runs can exceed a minute, so keep the actual screenshot "
        "and completed run available. Describe a withheld result honestly and inspect its "
        "stop reason. Do not depend on a fresh live agent run fitting inside the pitch."
    )
    doc.add_heading("Rehearsal and technology check", 1)
    doc.add_paragraph(
        "Practice the pitch using the slide timings in the recording plan. Rehearse each "
        "answer in 20–30 seconds, then stop for the next question. Confirm the session date, "
        "time, and link in the course Live Session tab. Join early and test microphone, "
        "camera, slide sharing, and a local PDF backup. Check public repository access "
        "before the session."
    )
    doc.add_heading("Feedback to request", 1)
    doc.add_paragraph(
        "Which evaluation would most convincingly establish that the model roles improve "
        "operator guidance over deterministic code alone? What evidence should precede "
        "expanding the forecasting scope?"
    )
    doc.save(OUTPUT / "DragonWings_Faculty_Showcase_Preparation.docx")


OUTPUT.mkdir(parents=True, exist_ok=True)
report()
recording_plan()
video_links()
faculty_brief()
print("Created report, recording plan, video-link document, and faculty brief")
