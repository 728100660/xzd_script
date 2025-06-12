# 测试边距
from xhtml2pdf import pisa


def html_to_pdf(html: str, output_path: str):
    full_html = """
<html>
<head>
<style>
    table { -pdf-keep-with-next: true; }
    p { margin: 0; -pdf-keep-with-next: true; }
</style>
</head>

<body>
    <p>Keepthesesetsof linesKeep these sets of linesKeep these sets of linesKeep these sets of linesKeep these sets of linesKeep these sets of linesKeep these sets of linesKeep these sets of linesKeep these sets of linesKeep these sets of lines</p>
    <p>KeepthesesetsofKeepthesesetsofKeepthesesetsofKeepthesesetsofKeepthesesetsofKee,pthesesetsofKeepthesesetsofKeepthesesetsofKeepthesesetsofKeepthesesetsofKeepthesesetsofKeepthesesetsof</p>
    <p>随着硬件技术的发展和算法的不断进步，大模型的应用前景非常广阔。在未来，大模型有望在更多的领域得到应用，如自动驾驶、医疗诊断等。同时，研究人员也在探索如何降低大模型的计算资源需求，提高其训练效率，以及如何使其更加易于解释和调试。</p>
    <p>随着硬件技术的发展和算法的不断进步，大模型的应用前景非常广阔。在未来，大模型有望在更多的领域得到应用，如自动驾驶、医疗诊断等。同时， 研究人员也在探索如何降低大模型的计算资源需求，提高其训练效率，以及如何使其更加易于解释和调试。</p>
    <p>may appear in a different frame</p>
    <p class="separator">&nbsp;<p>
</body>
</html>    
# 发现问题
测试了英文是没问题的，于是思考，是否是由于中文分隔符无法识别的问题。
于是上测试代码测试
# 解决办法
## 提前处理html内容
## 源码解决
"""
    with open(output_path, "wb") as f:
        pisa.CreatePDF(full_html, dest=f, encoding="UTF-8")
    print(f"PDF saved to: {output_path}")

if __name__ == "__main__":

    html_to_pdf("html", "output/output.pdf")
    # html_to_docx(html, "output/output.docx")