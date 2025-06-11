import markdown2
from weasyprint import HTML


def markdown_to_pdf(md_path, pdf_path):
    # 1. 读取 Markdown 内容
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # 2. 转为 HTML
    html_content = markdown2.markdown(md_content)

    # 3. 转为 PDF
    HTML(string=html_content).write_pdf(pdf_path)
    print(f"✅ PDF saved to {pdf_path}")


# 用法
markdown_to_pdf("markdown_test.md", "output.pdf")
