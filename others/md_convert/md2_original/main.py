from markdown import markdown
from xhtml2pdf import pisa
from html2docx import html2docx

import os
import re

def md_to_html(md_text: str) -> str:
    return markdown(md_text, output_format="html",
        extensions=["fenced_code", "tables", "codehilite"])

def html_to_pdf(html: str, output_path: str):
    chinese_punctuation = r'[，。！？；：、]'
    clean_html = re.sub(f"({chinese_punctuation})(?![\s\n<])", r"\1 ", html)
    with open(r"template.html", encoding="utf-8") as f:
        template = f.read()

    full_html = template.replace("{{ content }}", clean_html)
    with open(output_path, "wb") as f:
        pisa.CreatePDF(full_html, dest=f, encoding="UTF-8")
    print(f"PDF saved to: {output_path}")

def html_to_docx(html: str, output_path: str):

    docx_bytes = html2docx(html, "my_t")
    with open(output_path, "wb") as f:
        f.write(docx_bytes.getvalue())
    print(f"DOCX saved to: {output_path}")

if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)

    with open("markdown_test2.md", "r", encoding="utf-8") as f:
        md_text = f.read()

    html = md_to_html(md_text)

    html_to_pdf(html, "output/output.pdf")
    # html_to_docx(html, "output/output.docx")