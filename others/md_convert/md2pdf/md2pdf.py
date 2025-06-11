import re

import markdown
import pdfkit
from bs4 import BeautifulSoup
from html2docx import html2docx


# 替换 <details> 区块为普通内容
def remove_details(html):
    pattern = re.compile(
        r"<details>\s*<summary>(.*?)</summary>\s*(.*?)</details>",
        re.DOTALL
    )
    return pattern.sub(r"<p>\1</p>\2", html)


def md_to_pdf(md_path: str, output_path: str):
    # 读取 Markdown
    with open(md_path, encoding="utf-8") as f:
        md_text = f.read().strip()
    md_text = remove_details(md_text)

    # 解析 Markdown 为 HTML
    html_body = markdown.markdown(
        md_text,
        extensions=["fenced_code", "tables", "codehilite"]
    )

    # 读取 HTML 模板
    with open("template.html", encoding="utf-8") as f:
        template = f.read()

    # 替换 {{ content }}
    full_html = template.replace("{{ content }}", html_body)

    # 输出 PDF
    pdfkit.from_string(
        full_html,
        output_path,
        options={
            "enable-local-file-access": "",
            "quiet": "",
            "encoding": "utf-8",
            "enable-javascript": "",
            "javascript-delay": "1000",  # 等待 JS 执行
        }
    )
    print(f"✅ 成功生成：{output_path}")


def md_to_docx(md_path: str, output_path: str):
    # 读取 Markdown
    with open(md_path, encoding="utf-8") as f:
        md_text = f.read()
    md_text = remove_details(md_text)

    # 解析 Markdown 为 HTML
    html_body = markdown.markdown(
        md_text,
        extensions=["fenced_code", "tables", "codehilite"]
    )

    soup = BeautifulSoup(html_body, "html.parser")

    for pre in soup.find_all("pre"):
        # 提取 pre 中所有文本，包括换行
        text = pre.get_text()
        # 替换 pre 内容为纯文本，去掉 span
        pre.string = text

    clean_html = str(soup)

    docx = html2docx(clean_html, "my_docx_convert")

    with open(output_path, "wb") as f:
        f.write(docx.getvalue())
    print(f"✅ 成功生成：{output_path}")


if __name__ == "__main__":
    md_file = "markdown_test2.md"
    output_file = "markdown_test.pdf"
    output_file_docx = "markdown_test.docx"
    md_to_pdf(md_file, output_file)
    # md_to_docx(md_file, output_file_docx)
