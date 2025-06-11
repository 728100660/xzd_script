from markdown import markdown
from weasyprint import HTML

# 读取 markdown 文件
with open("input.md", "r", encoding="utf-8") as f:
    md_text = f.read()

# 转为 HTML
html = markdown(md_text, output_format="html5")

# 转为 PDF
HTML(string=html).write_pdf("/output/output.pdf")

print("✅ PDF 生成成功: /output/output.pdf")
