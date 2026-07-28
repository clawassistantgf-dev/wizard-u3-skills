---
name: markdown-to-email
description: "Use when replying by email and wanting to send HTML-formatted responses. Converts markdown to HTML, sends via direct smtplib Python script as multipart/alternative. Covers cron scheduling, SVG lead images, and DKIM deliverability."
version: 2.2.0
author: Bitcoin Wizard
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [email, markdown, html, conversion, smtplib, cron, deliverability]
    related_skills: [himalaya]
---

# Markdown to HTML Email — v2.2 (smtplib Pipeline)

## Overview

When Hermes replies by email, the built-in gateway sends only `text/plain`.
This skill overrides that by teaching the agent to write responses in markdown,
convert them to HTML via `md2email.py`, and send via **direct smtplib Python
script** as multipart/alternative (text/plain + text/html inline).

**Why smtplib instead of himalaya:** The himalaya CLI can fail silently -- SMTP
send succeeds but recipient never receives the email, especially across
providers (OVH -> Gmail). A direct smtplib script using the same credentials
from `~/.hermes/.env` is more reliable for cron-scheduled and one-shot sends.

## Limitations (tell the user explicitly)

| Limitation | Detail |
|---|---|
| Image generation | No FAL_KEY available -- create SVG banners instead |
| Meeting links | No Calendly/Google Calendar OAuth -- propose time slots manually |
| Cron delivery | no_agent scripts go in `~/.hermes/scripts/`, workdir goes elsewhere |
| Gmail deliverability | Without DKIM, Gmail may silently drop emails |
| Server paths | Users cannot see server file paths -- always deliver content inline |

## How It Works

```
Write markdown body
        |
        v
   python3 md2email.py            (markdown -> HTML)
        |
        v
   Python script builds MIME:
     - multipart/alternative (text/plain + text/html)
     - optional images/SVG attachments
     - recipients, CC, subject
        |
        v
   smtplib -> OVH SMTP -> recipient inbox
```

## Core Files

| File | Location | Purpose |
|---|---|---|
| md2email.py | `scripts/md2email.py` | Converts markdown to email-safe HTML (pure Python) |
| SVG banner template | `references/svg-banner-template.md` | SVG lead image for prospecting emails |
| Mermaid diagram | `references/mermaid-architecture.md` | Architecture diagram for technical leads |
| DNS deliverability | `references/dns-deliverability.md` | DKIM/SPF/DMARC diagnostics via DNS-over-HTTPS |
| LaTeX-to-PDF compilation | `references/latex-to-pdf-compilation.md` | Compile .tex to PDF without TeX installation |

## Workflow -- One-Shot SMTP Send

### Step 1: Write markdown content inline

Always keep the content inline in the response so the user can see and edit it.

### Step 2: Convert to HTML

```bash
HTML_CONTENT=$(python3 /home/hermes/.hermes/skills/email/markdown-to-email/scripts/md2email.py <<< "$MD_CONTENT")
```

### Step 3: Build and send via Python SMTP

```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
import smtplib, ssl

msg = MIMEMultipart()
msg["From"] = user
msg["To"] = ", ".join(to_addrs)
msg["Cc"] = ", ".join(cc_addrs)
msg["Subject"] = subject
msg["Date"] = formatdate(localtime=True)

alt = MIMEMultipart("alternative")
alt.attach(MIMEText(md_body, "plain", "utf-8"))
alt.attach(MIMEText(html_body, "html", "utf-8"))
msg.attach(alt)

ctx = ssl.create_default_context()
smtp = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
smtp.ehlo()
smtp.starttls(context=ctx)
smtp.ehlo()
smtp.login(user, password)
smtp.sendmail(user, all_recipients, msg.as_string())
smtp.quit()
```

### Step 4: Gateway response -- clean text only

The Hermes gateway always sends a plain-text copy. Write it as clean prose
with NO markdown syntax so raw formatting chars do not leak.

```
HTML version sent via direct SMTP -- check your inbox.
```

## Workflow -- Cron-Scheduled Send

### Setup

1. Create the Python script (self-contained: reads .env, builds MIME, sends)
2. Copy it to `~/.hermes/scripts/<name>.py`
3. Schedule via cronjob tool:

```
cronjob(
    action="create",
    name="Email campaign name",
    schedule="2026-07-13T08:00:00",  # ISO timestamp = UTC
    script="script_name.py",         # relative to ~/.hermes/scripts/
    workdir="/path/to/data/files",
    no_agent=True,
    deliver="origin",
)
```

### Script must

- Read credentials from `~/.hermes/.env` (parse KEY=VAL lines)
- Use absolute paths for everything (cron CWD is workdir, not guaranteed)
- sys.exit(0) on success, sys.exit(1) on failure
- Print status to stdout (becomes cron delivery text)

## Deliverability Pitfalls

### 1. DKIM required for Gmail

Without a DKIM TXT record on the sending domain, **Gmail silently drops
emails**. The SMTP server returns "OK" but the message never reaches the
recipient. No bounce-back is generated.

Check DNS via Google DNS-over-HTTPS:

```
curl -s "https://dns.google/resolve?name=DOMAIN&type=TXT"
curl -s "https://dns.google/resolve?name=_dmarc.DOMAIN&type=TXT"
```

### 2. SPF too strict

`-all` (hard fail) means only authorized IPs can send. If the relay is not
in the SPF include, Gmail rejects. Use `~all` (soft fail) for testing.

### 3. OVH folder naming

OVH IMAP uses `INBOX.Sent`, `INBOX.Drafts`, not bare `Sent`.

### 4. No sudo access

The Hermes adapter at `/usr/local/lib/hermes-agent/` is root-owned. Do not
attempt to patch it -- use smtplib scripts instead.

## LaTeX-to-PDF Compilation (Without TeX)

When a `.tex` file must be compiled to PDF and `pdflatex` is unavailable,
use `scripts/latex_to_pdf.py` which parses LaTeX via regex and renders via
WeasyPrint. Limitations: math renders as italic text, cross-references are
stripped, complex environments may lose structure. Enough for reading but
not for journal submission. See `references/latex-to-pdf-compilation.md`.

## Lead Prospecting Email Pattern

### Structure

1. Accroche -- why they should care about workflow automation
2. Le constat -- what repetitive tasks cost them
3. La solution -- Workflow Agents + Harnais Agentique
4. Exemples concrets -- tailored to their industry (Web3, SaaS, etc.)
5. Prochaine etape -- 3 time slots + call to action
6. Signature: Bitcoin Wizard -- Agent Hermes / Nous Research

### Image (when FAL_KEY is absent)

Create an SVG banner inline. Key elements:
- Dark theme (#0d1117, #161b22)
- Bitcoin orange accent (#f7931a)
- Blue tech accent (#58a6ff)
- Hermes caduceus staff as logo
- Feature badges (pill-shaped, 130x24px rounded)

Attach as `MIMEImage(_subtype="svg+xml")` and reference via `cid:` in HTML.

## User Preference -- File Paths

**NEVER give the user a server-local file path.** They cannot see your
filesystem. Always deliver content inline in the message body.

## Verification Checklist

- [ ] Markdown written inline (user can see and edit)
- [ ] HTML generated via md2email.py
- [ ] smtplib script sends without errors
- [ ] Gateway response is clean plain text (no markdown chars)
- [ ] DKIM on sending domain (or warn about Gmail blocking)
- [ ] Cron job: script in ~/.hermes/scripts/, workdir for data files