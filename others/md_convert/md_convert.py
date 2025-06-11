import re

import markdown

from others.md_convert.md2pdf.md2pdf import md_to_pdf


# 替换 <details> 区块为普通内容
def remove_details(html):
    pattern = re.compile(
        r"<details>\s*<summary>(.*?)</summary>\s*(.*?)</details>",
        re.DOTALL
    )
    return pattern.sub(r"<h3>\1</h3>\2", html)


def md_to_html(md_path: str):
    # 读取 Markdown
    with open(md_path, encoding="utf-8") as f:
        md_text = f.read()
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
    return full_html




if __name__ == "__main__":
    md_file = "markdown_test.md"
    output_file = "markdown_test.pdf"
    full_html = md_to_html(md_file)
    md_to_pdf(full_html, output_file)
