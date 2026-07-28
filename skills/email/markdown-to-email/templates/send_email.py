#!/usr/bin/env python3
"""
send_scheduled_email.py - Template for sending HTML emails via direct SMTP.

Reads credentials from ~/.hermes/.env.
Builds multipart/alternative (text/plain + text/html).
Optionally attaches SVG/MIMEImage files.
Sends via smtplib (stdlib - no dependencies).

Usage:
    python3 send_scheduled_email.py

For cron: copy to ~/.hermes/scripts/ and use cronjob(script="...", no_agent=True)
"""

import os
import smtplib
import ssl
import subprocess
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import formatdate
from pathlib import Path

# Paths
HERMES_HOME = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")))
ENV_FILE = HERMES_HOME / ".env"
SKILL_DIR = HERMES_HOME / "skills" / "email" / "markdown-to-email"


def load_env():
    """Read credentials from Hermes .env file."""
    if not ENV_FILE.exists():
        print(f"[ERROR] .env not found: {ENV_FILE}", file=sys.stderr)
        sys.exit(1)
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


def get_cred(key):
    val = os.getenv(key, "").strip()
    if not val:
        print(f"[ERROR] {key} not set", file=sys.stderr)
        sys.exit(1)
    return val


def md_to_html(md_text):
    """Convert markdown to HTML via md2email.py."""
    script = SKILL_DIR / "scripts" / "md2email.py"
    if not script.exists():
        print(f"[WARN] md2email.py not found at {script}", file=sys.stderr)
        return None
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            input=md_text, capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    except Exception as e:
        print(f"[WARN] md2email.py error: {e}", file=sys.stderr)
    return None


def build_and_send(from_addr, to_addrs, cc_addrs, subject, md_body, svg_path=None):
    """Build multipart/alternative email and send via SMTP."""
    smtp_host = get_cred("EMAIL_SMTP_HOST")
    smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    smtp_pass = get_cred("EMAIL_PASSWORD")

    msg = MIMEMultipart("mixed")
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    msg["Cc"] = ", ".join(cc_addrs)
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = (
        f"<hermes-{datetime.now().strftime('%Y%m%d%H%M%S')}@"
        f"{from_addr.split('@')[-1]}>"
    )

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(md_body, "plain", "utf-8"))
    html = md_to_html(md_body)
    if html:
        alt.attach(MIMEText(html, "html", "utf-8"))
    msg.attach(alt)

    if svg_path and Path(svg_path).exists():
        with open(svg_path, "rb") as f:
            svg_part = MIMEImage(f.read(), _subtype="svg+xml", name=Path(svg_path).name)
        svg_part.add_header("Content-Disposition", f"attachment; filename={Path(svg_path).name}")
        svg_part.add_header("Content-ID", "<hermesdeck-banner>")
        msg.attach(svg_part)

    all_recipients = to_addrs + cc_addrs
    ctx = ssl.create_default_context()
    smtp = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
    smtp.ehlo()
    smtp.starttls(context=ctx)
    smtp.ehlo()
    smtp.login(from_addr, smtp_pass)
    smtp.sendmail(from_addr, all_recipients, msg.as_string())
    smtp.quit()
    print(f"[OK] Email sent to {len(all_recipients)} recipient(s)")
    return True


if __name__ == "__main__":
    # --- CONFIGURE HERE ---
    load_env()
    from_addr = get_cred("EMAIL_ADDRESS")
    to_addrs = ["recipient1@example.com", "recipient2@example.com"]
    cc_addrs = ["cc@example.com"]
    subject = "Your subject line here"

    md_body = """# Subject

**Markdown** content here.

- List item
- Another item

> Blockquote

Signature
"""
    svg_path = None  # or "/path/to/banner.svg"

    build_and_send(from_addr, to_addrs, cc_addrs, subject, md_body, svg_path)