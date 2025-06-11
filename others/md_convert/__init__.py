import markdown
import pdfkit

# 加载 markdown 文件
with open("markdown_test.md", encoding="utf-8") as f:
    md_text = f.read()

html_template = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Arial'; margin: 2em; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; }}
    pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; }}
    h1, h2 {{ color: #2c3e50; }}
  </style>
</head>
<body>
{markdown.markdown(md_text, extensions=["fenced_code", "tables"])}
</body>
</html>
"""

pdfkit.from_string(html_template, "output_wkhtmltopdf3.pdf")


html_content = markdown.markdown(
    md_text,
    extensions=["fenced_code", "tables"]
)

html_template = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Arial'; margin: 2em; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; }}
    pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; }}
    h1, h2 {{ color: #2c3e50; }}
  </style>
  <!-- 加入 MathJax -->
  <script type="text/javascript" async
    src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js">
  </script>
</head>
<body>
{html_content}
</body>
</html>
"""

pdfkit.from_string(html_template, "output_wkhtmltopdf3_math.pdf", options={"enable-local-file-access": ""})
