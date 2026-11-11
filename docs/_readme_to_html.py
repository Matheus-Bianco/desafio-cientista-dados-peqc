import os
import re
import markdown

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
SRC = os.path.join(RAIZ, "README.md")
OUT = os.path.join(RAIZ, "_readme_render.html")

with open(SRC, encoding="utf-8") as f:
    texto = f.read()

# extrai blocos mermaid para nao passar pelo conversor de markdown
mermaids = []


def _guarda(m):
    mermaids.append(m.group(1))
    return f"@@MERMAID{len(mermaids) - 1}@@"


texto = re.sub(r"```mermaid\n(.*?)```", _guarda, texto, flags=re.DOTALL)

html_corpo = markdown.markdown(
    texto,
    extensions=["tables", "fenced_code", "sane_lists", "attr_list", "toc"],
)

# devolve os blocos mermaid como <pre class="mermaid">
for i, src in enumerate(mermaids):
    bloco = f'<div class="mermaid-wrap"><pre class="mermaid">{src}</pre></div>'
    html_corpo = html_corpo.replace(f"<p>@@MERMAID{i}@@</p>", bloco)
    html_corpo = html_corpo.replace(f"@@MERMAID{i}@@", bloco)

TPL = """<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<title>README - Desafio RMI</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{ --pri:#1e3a8a; --tx:#1f2937; --mut:#6b7280; --bd:#e5e7eb; --bg:#ffffff; --code:#eef2ff; }
*{ box-sizing:border-box; }
html{ -webkit-print-color-adjust:exact; print-color-adjust:exact; }
body{ font-family:'Inter',system-ui,sans-serif; color:var(--tx); line-height:1.6; max-width:860px; margin:0 auto; padding:24px 28px; font-size:14.5px; }
h1{ color:var(--pri); font-size:26px; border-bottom:3px solid var(--pri); padding-bottom:8px; margin:6px 0 16px; }
h2{ color:var(--pri); font-size:19px; margin:30px 0 10px; }
h3{ color:var(--tx); font-size:16px; margin:20px 0 8px; }
a{ color:var(--pri); text-decoration:none; }
p{ margin:10px 0; }
ul,ol{ margin:10px 0; padding-left:22px; }
li{ margin:4px 0; }
hr{ border:none; border-top:1px solid var(--bd); margin:22px 0; }
code{ font-family:'JetBrains Mono',monospace; background:var(--code); color:#3730a3; padding:1px 5px; border-radius:4px; font-size:12.5px; }
pre{ background:#0f172a; color:#e2e8f0; padding:14px 16px; border-radius:8px; overflow:auto; font-size:12.5px; line-height:1.5; }
pre code{ background:none; color:inherit; padding:0; }
table{ border-collapse:collapse; width:100%; margin:14px 0; font-size:13px; }
th{ background:var(--pri); color:#fff; text-align:left; padding:8px 10px; font-weight:600; }
td{ border:1px solid var(--bd); padding:7px 10px; vertical-align:top; }
tr:nth-child(even) td{ background:#f8fafc; }
td code{ font-size:11.5px; white-space:nowrap; }
.mermaid-wrap{ background:#f8fafc; border:1px solid var(--bd); border-radius:10px; padding:14px; margin:16px 0; text-align:center; }
.mermaid{ background:none; color:inherit; padding:0; }
img{ max-width:100%; border:1px solid var(--bd); border-radius:8px; }
strong{ font-weight:600; }
em{ color:var(--mut); }
@page{ size:A4; margin:14mm; }
h2,h3{ break-after:avoid; }
table,pre,.mermaid-wrap,img{ break-inside:avoid; }
</style>
</head>
<body>
__CORPO__
<script type="module">
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
mermaid.initialize({ startOnLoad:true, theme:'neutral', flowchart:{ htmlLabels:true, useMaxWidth:true } });
</script>
</body>
</html>"""

html = TPL.replace("__CORPO__", html_corpo)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("OK:", OUT)
