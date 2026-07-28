#!/usr/bin/env python3
"""
latex_to_pdf.py — WeasyPrint-based LaTeX-to-PDF compiler.

Usage: python3 latex_to_pdf.py input.tex output.pdf

Reads a .tex file, converts it to HTML with basic LaTeX parsing,
and renders to PDF via WeasyPrint. No texlive installation needed.

Pipelines: .tex -> Python regex -> HTML -> WeasyPrint -> .pdf

Requires: weasyprint (pip install --user --break-system-packages weasyprint)
"""

import re, sys
from pathlib import Path
import weasyprint


def latex_to_html(tex: str) -> str:
    """Convert LaTeX document to HTML with CSS for A4 printing."""
    lines = tex.split('\n')
    out = []
    out.append("""<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
<style>
@page{size:A4;margin:2.5cm}
body{font-family:'DejaVu Serif',serif;font-size:11pt;line-height:1.6}
h1{font-size:18pt;margin:1.5em 0 0.5em}
h2{font-size:14pt;margin:1.2em 0 0.3em}
h3{font-size:12pt;margin:1em 0 0.3em}
p{text-align:justify;margin:0.4em 0;text-indent:1.5em}
tt{font-family:'DejaVu Sans Mono',monospace;font-size:9pt}
</style></head><body>""")

    def clean(t):
        # Order matters: multi-char before single-char
        t = re.sub(r'\\leanfile\{([^}]*)\}', r'[\1]', t)
        t = re.sub(r'\\lean\{([^}]*)\}', r'[Lean: \1]', t)
        t = re.sub(r'\\texttt\{([^}]*)\}', r'<tt>\1</tt>', t)
        t = re.sub(r'\\textbf\{([^}]*)\}', r'<b>\1</b>', t)
        t = re.sub(r'\\emph\{([^}]*)\}', r'<i>\1</i>', t)
        t = re.sub(r'\\textit\{([^}]*)\}', r'<i>\1</i>', t)
        t = re.sub(r'\\textnormal\{([^}]*)\}', r'\1', t)
        t = re.sub(r'\\text\{([^}]*)\}', r'\1', t)
        t = re.sub(r'\\mathrm\{([^}]*)\}', r'\1', t)
        t = re.sub(r'\\operatorname\{([^}]*)\}', r'\1', t)
        t = re.sub(r'\\ind\{([^}]*)\}', r'1_{\1}', t)
        t = re.sub(r'\\card\{([^}]*)\}', r'|\1|', t)
        t = re.sub(r'\\cite\{[^}]*\}', '', t)
        t = re.sub(r'\\label\{[^}]*\}', '', t)
        t = re.sub(r'\\ref\{[^}]*\}', '(ref)', t)
        t = re.sub(r'\$\$([^$]*)\$\$', r'<i>\1</i>', t)
        t = re.sub(r'\$([^$]*)\$', r'<i>\1</i>', t)
        t = re.sub(r'\\\[([^\]]*)\\\]', r'<br><i>\1</i><br>', t)
        t = re.sub(r'\\\(([^)]*)\\\)', r'<i>\1</i>', t)
        for cmd, repl in [('\\sum','sum'),('\\prod','prod'),('\\to','->'),
                ('\\mapsto','->'),('\\in',' in '),('\\notin',' not in '),
                ('\\subseteq',' subset '),('\\setminus','\\'),
                ('\\cup',' U '),('\\cap',' n '),('\\coloneqq',' := '),
                ('\\times','x'),('\\cdot','.'),('\\neq','!='),
                ('\\geq','>='),('\\leq','<='),('\\oplus',' xor '),
                ('\\otimes',' @ '),('\\sim','~'),('\\simeq','~='),
                ('\\cong','~='),('\\mid','|'),('\\colon',':'),
                ('\\\\','<br>'),('\\longrightarrow','->'),('\\rightarrow','->'),
                ('\\Rightarrow','=>'),('\\Leftrightarrow','<=>')]:
            t = t.replace(cmd, repl)
        t = re.sub(r'\\(varphi|eta|iota|alpha|beta|gamma|delta|omega|sigma)\b',
                   lambda m: {'varphi':'phi','eta':'eta','iota':'iota'}.get(m.group(1), m.group(1)), t)
        t = re.sub(r'\\[{}]', '', t)
        t = re.sub(r'\\og\s*', '"<<', t); t = re.sub(r'\\fg\s*', '">>', t)
        t = re.sub(r'\\[;,:\!\s]+', ' ', t)
        t = re.sub(r'\\quad\s*', '  ', t); t = re.sub(r'\\qquad\s*', '    ', t)
        t = re.sub(r'\\noindent', '', t); t = re.sub(r'\\left|\\right', '', t)
        t = re.sub(r"\\'([aeiou])", lambda m: m.group(1)+"'", t)
        t = re.sub(r"\\`([aeiou])", lambda m: m.group(1), t)
        t = re.sub(r'\\\^([aeiou])', lambda m: m.group(1)+'^', t)
        t = re.sub(r'\\"([aeiouy])', lambda m: m.group(1)+'"', t)
        t = re.sub(r'\\c\{c\}', 'c', t); t = re.sub(r'\\oe', 'oe', t)
        t = re.sub(r'\\texorpdfstring\{[^}]*\}\{[^}]*\}', '', t)
        t = re.sub(r'\\([a-zA-Z]+)', '', t)
        t = re.sub(r'  +', ' ', t)
        t = re.sub(r'\s+([.,;:!?])', r'\1', t)
        t = re.sub(r' ,', ',', t); t = re.sub(r' \.', '.', t)
        return t.strip()

    i, in_doc = 0, False
    while i < len(lines):
        s = lines[i].strip()
        if '\\begin{document}' in s:
            in_doc = True
            out.append('<div class="title-page"><h1>La couverture double par cycles</h1>'
                       '<p style="font-style:italic">Trait\u00e9 formel</p></div>')
            i += 1; continue
        if '\\end{document}' in s: break
        if not in_doc or s.startswith('%'): i += 1; continue
        if s in ['\\maketitle','\\tableofcontents']: i += 1; continue
        if re.match(r'\\begin\{|\\end\{', s): i += 1; continue
        if s.startswith('\\(') or s.startswith('\\)') or s in ['\\[','\\]']: i += 1; continue
        m = re.match(r'\\(sub)*section\{([^}]*)\}', s)
        if m:
            level = 2 if m.group(1) else 1 if m.group(0).startswith('\\section') else 3
            tag = ['h1','h2','h3'][min(level-1,2)]
            out.append(f'<{tag}>{clean(m.group(2))}</{tag}>')
            i += 1; continue
        if s and not s.startswith('\\'):
            out.append(f'<p>{clean(s)}</p>')
        i += 1

    out.append("</body></html>")
    return '\n'.join(out)


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} input.tex output.pdf", file=sys.stderr)
        sys.exit(1)
    tex = Path(sys.argv[1]).read_text(encoding='utf-8')
    html = latex_to_html(tex)
    Path(sys.argv[1]+'.html').write_text(html, encoding='utf-8')  # debug output
    weasyprint.HTML(string=html).write_pdf(sys.argv[2])
    print(f"[OK] {sys.argv[2]} ({Path(sys.argv[2]).stat().st_size} bytes, {html.count('<p>')} paragraphs)")
    return 0


if __name__ == '__main__':
    sys.exit(main())