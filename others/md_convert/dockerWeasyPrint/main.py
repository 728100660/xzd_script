import os
from markdown import markdown
from weasyprint import HTML
from html2docx import html2docx

def convert_md_to_html(md_text):
    return markdown(md_text, output_format="html")

def save_pdf_from_html(html, output_path):
    HTML(string=html).write_pdf(output_path)
    print(f"PDF saved to: {output_path}")

def save_docx_from_html(html, output_path):
    docx_bytes = html2docx(html, "tt")
    with open(output_path, "wb") as f:
        f.write(docx_bytes.getvalue())
    print(f"DOCX saved to: {output_path}")

if __name__ == "__main__":
    input_file = "input.md"
    with open(input_file, "r", encoding="utf-8") as f:
        md_text = f.read()

    html = convert_md_to_html(md_text)
    os.makedirs("output", exist_ok=True)

    save_pdf_from_html(html, "output/output.pdf")
    save_docx_from_html(html, "output/output.docx")
