# LaTeX-to-PDF Compilation Without TeX

When `pdflatex` / `xelatex` / `lualatex` are unavailable (no sudo, no
texlive installed), compile LaTeX documents to PDF via a two-step pipeline:

## Pipeline

```
.tex source
    |
    v
Python regex parser  (strip LaTeX commands, extract text with structure)
    |
    v
HTML document        (with CSS for A4/page styling)
    |
    v
weasyprint           (Python HTML/CSS-to-PDF renderer)
    |
    v
PDF file             (~90 KB for a 60 KB .tex, 500+ paragraphs)
```

## Installation (once)

```bash
pip install --user --break-system-packages weasyprint
```

## Key Parser Rules

Order matters in regex substitution — multi-char commands must be handled
before single-char fallthrough:

1. **Known commands with arguments** — `\textbf{text}`, `\emph{text}`,
   `\texttt{text}`, `\lean{ref}`, `\leanfile{path}`, `\card{arg}`,
   `\deg{arg}` — convert to HTML tags or plain text.

2. **Citations and refs** — `\cite{...}` (strip), `\ref{...}` (replace with
   "(ref)" or specific number), `\label{...}` (strip).

3. **Math delimiters** — `$...$`, `$$...$$`, `\[...\]`, `\(...\)` — wrap
   content in `<i>...</i>` (italic approximation for inline math).

4. **Named math operators** — `\sum`, `\prod`, `\to`, `\mapsto`, `\in`,
   `\subseteq`, `\coloneqq`, `\times`, `\cdot`, `\sim`, `\simeq`, `\Gamma`,
   `\varphi`, `\eta`, `\iota`, etc. — replace with Unicode or ASCII equivalents.

5. **French accents** — `\'e`, `\`e`, `\^e`, `\c{c}`, `\"u`, etc. —
   handl via Unicode substitution.

6. **Special form** — `\texorpdfstring{tex}{pdf}` — strip entirely
   (for hyperref compatibility).

7. **Catch-all** — remaining `\command` patterns — strip the command name.

8. **Cleanup** — collapse double spaces, fix punctuation spacing.

## Environment Handling

LaTeX environments like `\begin{theoreme}...\end{theoreme}` are handled by
**skipping the boundary lines** — the content between them is processed as
regular paragraphs. Environment-specific styling (theorems, definitions,
proofs) is applied via CSS classes on the HTML side.

## CSS for A4 Output

```css
@page { size: A4; margin: 2.5cm; }
body { font-family: 'DejaVu Serif', serif; font-size: 11pt; line-height: 1.6; }
h1 { font-size: 18pt; margin: 1.5em 0 0.5em; }
h2 { font-size: 14pt; margin: 1.2em 0 0.3em; }
p { text-align: justify; margin: 0.4em 0; text-indent: 1.5em; }
```

## Known Limitations

| Issue | Cause | Mitigation |
|---|---|---|
| Math rendered as plain text | No LaTeX math engine | Wraps in `<i>` — readable but not typeset |
| Environment structure lost | No nesting tracking | CSS styling on surrounding divs |
| Missing figures/tables | No float handling | Extract and inline as HTML img |
| `\ref` resolution lost | Cross-references stripped | Hardcode key refs (e.g. `\ref{thm:principal}` -> "1") |
| Bracket-depth errors | Complex nested `{...}` | Test output manually and fix edge cases |

## Testing Output

```bash
# Check for remaining LaTeX artifacts
grep -c '\texorpdfstring\|\\.*\{' output.html
grep -c '\.lean\.lean' output.html  # double suffix bug
grep 'Jaeger\|cycleDoubleCover\|Nash-Williams' output.html  # key content present
```

## WeasyPrint Rendering

```python
import weasyprint
weasyprint.HTML(string=html).write_pdf("output.pdf")
```

For very large documents, write HTML to a file first and pass the path —
weasyprint handles both string and file inputs.

## When to Use This vs Real LaTeX

| Situation | Recommendation |
|---|---|
| pdflatex available | Use real LaTeX |
| TeX not installed, no sudo | Use this pipeline |
| Document has heavy math/figures | Accept degraded math, or request sudo install texlive |
| Document is simple text + theorems | This pipeline works well (~90% fidelity) |
| Need professional typesetting (journal submission) | Must install texlive or compile externally |