#!/usr/bin/env python3
"""
md2email.py — Convert Markdown to email-safe HTML.

Pure Python stdlib, zero dependencies.
Reads markdown from stdin, writes HTML to stdout.

Usage:
    cat response.md | python3 md2email.py > email.html
    echo "**bold** text" | python3 md2email.py
"""

import sys
import re
import html


def escape(text):
    """Escape HTML special characters."""
    return html.escape(text)


def inline_convert(text):
    """Convert inline markdown formatting to HTML."""
    # Escape HTML first, then apply markdown patterns
    text = escape(text)

    # Inline code: `code`  (must be done before other patterns)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    # Bold: **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)

    # Italic: *text* or _text_ (but not _ inside words like_snake_case)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'(?<!_)_(?!_)(.+?)(?<!_)_(?!_)', r'<em>\1</em>', text)

    # Strikethrough: ~~text~~
    text = re.sub(r'~~(.+?)~~', r'<del>\1</del>', text)

    # Images: ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" style="max-width:100%;height:auto;">', text)

    # Links: [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)

    return text


def convert_markdown(text):
    """Convert markdown text to full HTML email."""
    lines = text.split('\n')

    output_parts = []
    in_code_block = False
    code_block_lang = ""
    code_lines = []
    in_paragraph = False
    in_list = False
    list_type = None  # 'ul' or 'ol'
    in_blockquote = False
    blockquote_lines = []

    def flush_code():
        nonlocal code_lines
        if not code_lines:
            return
        lang_attr = f' class="language-{code_block_lang}"' if code_block_lang else ''
        code_html = ''.join(code_lines)
        output_parts.append(f'<pre><code{lang_attr}>{code_html}</code></pre>\n')
        code_lines = []

    def flush_paragraph():
        nonlocal in_paragraph
        if in_paragraph:
            # Close the paragraph tag
            output_parts.append('</p>\n')
            in_paragraph = False

    def flush_list():
        nonlocal in_list, list_type
        if in_list:
            output_parts.append(f'</{list_type}>\n')
            in_list = False
            list_type = None

    def flush_blockquote():
        nonlocal in_blockquote, blockquote_lines
        if in_blockquote:
            content = '\n'.join(blockquote_lines)
            output_parts.append(f'<blockquote>\n{content}\n</blockquote>\n')
            blockquote_lines = []
            in_blockquote = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # --- Code blocks ---
        if stripped.startswith('```'):
            if in_code_block:
                flush_code()
                in_code_block = False
                code_block_lang = ""
            else:
                flush_paragraph()
                flush_list()
                flush_blockquote()
                in_code_block = True
                code_block_lang = stripped[3:].strip()
            i += 1
            continue

        if in_code_block:
            code_lines.append(escape(line) + '\n')
            i += 1
            continue

        # --- Horizontal rule ---
        if re.match(r'^-{3,}$', stripped) or re.match(r'^\*{3,}$', stripped) or re.match(r'^_{3,}$', stripped):
            flush_paragraph()
            flush_list()
            flush_blockquote()
            output_parts.append('<hr>\n')
            i += 1
            continue

        # --- Empty line ---
        if stripped == '':
            flush_paragraph()
            flush_list()
            flush_blockquote()
            i += 1
            continue

        # --- Headers ---
        h_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if h_match:
            flush_paragraph()
            flush_list()
            flush_blockquote()
            level = len(h_match.group(1))
            content = inline_convert(h_match.group(2))
            output_parts.append(f'<h{level}>{content}</h{level}>\n')
            i += 1
            continue

        # --- Blockquotes ---
        if stripped.startswith('> '):
            flush_paragraph()
            flush_list()
            in_blockquote = True
            # Process the blockquote content inline
            bq_content = re.sub(r'^>\s?', '', line)
            blockquote_lines.append(inline_convert(bq_content))
            i += 1
            continue

        # --- Unordered list ---
        ul_match = re.match(r'^(\s*)[-*+]\s+(.+)$', line)
        if ul_match:
            flush_paragraph()
            flush_blockquote()
            indent = len(ul_match.group(1))
            content = inline_convert(ul_match.group(2))
            if not in_list or list_type != 'ul':
                flush_list()
                output_parts.append('<ul>\n')
                in_list = True
                list_type = 'ul'
            output_parts.append(f'<li>{content}</li>\n')
            i += 1
            continue

        # --- Ordered list ---
        ol_match = re.match(r'^(\s*)\d+\.\s+(.+)$', line)
        if ol_match:
            flush_paragraph()
            flush_blockquote()
            indent = len(ol_match.group(1))
            content = inline_convert(ol_match.group(2))
            if not in_list or list_type != 'ol':
                flush_list()
                output_parts.append('<ol>\n')
                in_list = True
                list_type = 'ol'
            output_parts.append(f'<li>{content}</li>\n')
            i += 1
            continue

        # --- Regular paragraph text ---
        flush_list()
        flush_blockquote()
        if not in_paragraph:
            output_parts.append('<p>')
            in_paragraph = True
            output_parts.append(inline_convert(stripped))
        else:
            output_parts.append(' ')
            # Preserve line breaks within paragraphs
            output_parts.append('<br>\n')
            output_parts.append(inline_convert(stripped))
        i += 1

    # Flush any remaining open blocks
    flush_code()
    flush_paragraph()
    flush_list()
    flush_blockquote()

    body = ''.join(output_parts)

    # Wrap in email-safe HTML template
    html_output = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light dark">
<style type="text/css">
/* Email-safe inline styles */
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    font-size: 16px;
    line-height: 1.6;
    color: #1a1a1a;
    max-width: 640px;
    margin: 0 auto;
    padding: 20px;
}}
h1 {{ font-size: 1.8em; margin: 1.2em 0 0.6em; color: #111; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }}
h2 {{ font-size: 1.5em; margin: 1.1em 0 0.5em; color: #222; }}
h3 {{ font-size: 1.3em; margin: 1em 0 0.5em; color: #333; }}
h4 {{ font-size: 1.1em; margin: 0.9em 0 0.4em; color: #444; }}
h5, h6 {{ font-size: 1em; margin: 0.8em 0 0.4em; color: #555; }}
p {{ margin: 0.8em 0; }}
a {{ color: #1a73e8; text-decoration: underline; }}
code {{
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    font-size: 0.9em;
    background: #f4f4f4;
    padding: 2px 6px;
    border-radius: 3px;
}}
pre {{
    background: #f6f8fa;
    border: 1px solid #e1e4e8;
    border-radius: 6px;
    padding: 16px;
    overflow-x: auto;
    margin: 1em 0;
}}
pre code {{
    background: none;
    padding: 0;
    border-radius: 0;
    font-size: 0.85em;
    line-height: 1.45;
    color: #24292e;
    white-space: pre;
}}
blockquote {{
    margin: 1em 0;
    padding: 0.5em 1em;
    border-left: 4px solid #d0d7de;
    background: #f6f8fa;
    color: #57606a;
}}
blockquote p {{ margin: 0.3em 0; }}
ul, ol {{ margin: 0.5em 0; padding-left: 2em; }}
li {{ margin: 0.3em 0; }}
hr {{ border: none; border-top: 2px solid #e1e4e8; margin: 1.5em 0; }}
img {{ max-width: 100%; height: auto; border-radius: 4px; }}
del {{ color: #888; }}
strong {{ font-weight: 600; }}
em {{ font-style: italic; }}
/* Dark mode support */
@media (prefers-color-scheme: dark) {{
    body {{ color: #e6e6e6; background: #0d1117; }}
    h1 {{ color: #f0f0f0; border-bottom-color: #30363d; }}
    h2 {{ color: #e0e0e0; }}
    h3 {{ color: #d0d0d0; }}
    h4, h5, h6 {{ color: #c0c0c0; }}
    a {{ color: #58a6ff; }}
    code {{ background: #161b22; color: #c9d1d9; }}
    pre {{ background: #161b22; border-color: #30363d; }}
    pre code {{ color: #c9d1d9; }}
    blockquote {{ border-left-color: #30363d; background: #161b22; color: #8b949e; }}
    hr {{ border-top-color: #30363d; }}
    del {{ color: #777; }}
}}
</style>
</head>
<body>
{body}
</body>
</html>"""

    return html_output


def main():
    text = sys.stdin.read()
    if not text.strip():
        print("Usage: cat response.md | python3 md2email.py > email.html", file=sys.stderr)
        sys.exit(1)
    html = convert_markdown(text)
    sys.stdout.write(html)


if __name__ == '__main__':
    main()