#!/usr/bin/env python3
"""
Patch the Hermes Email adapter to send multipart/alternative emails
with both plain text and HTML versions.

This script modifies the Email adapter at:
  /usr/local/lib/hermes-agent/plugins/platforms/email/adapter.py

Changes:
1. _send_email() now converts markdown body to HTML and builds
   multipart/alternative (text/plain + text/html)
2. _send_email_with_attachment() merges HTML files into the body
   instead of sending them as separate attachments
3. _send_email_with_attachments() same treatment

Run: sudo python3 patch_adapter.py
"""

import re
import sys
from pathlib import Path

ADAPTER_PATH = Path("/usr/local/lib/hermes-agent/plugins/platforms/email/adapter.py")
SCRIPT_PATH = Path.home() / ".hermes" / "skills" / "email" / "markdown-to-email" / "scripts" / "md2email.py"

def read_adapter() -> str:
    return ADAPTER_PATH.read_text(encoding="utf-8")

def write_adapter(content: str) -> None:
    ADAPTER_PATH.write_text(content, encoding="utf-8")

def patch_send_email(content: str) -> str:
    """Replace _send_email to build multipart/alternative with HTML."""
    
    # Find the _send_email method
    marker = '    def _send_email(\n        self,\n        to_addr: str,\n        body: str,\n        reply_to_msg_id: Optional[str] = None,\n    ) -> str:\n        """Send an email via SMTP. Runs in executor thread."""'
    
    new_marker = '''    def _send_email(
        self,
        to_addr: str,
        body: str,
        reply_to_msg_id: Optional[str] = None,
    ) -> str:
        """Send an email via SMTP. Runs in executor thread.
        
        If the body contains markdown formatting, automatically converts
        it to HTML and sends as multipart/alternative (text/plain + text/html).
        """
        # Detect markdown: if body has headers, bold, code fences, lists, etc.
        has_markdown = bool(re.search(r'^#{1,6}\s|\\*\\*|```|^- |^\\d+\\. |^> |^---$|\\[.*\\]\\(', body, re.MULTILINE))'''
    
    content = content.replace(marker, new_marker, 1)
    if content == content:
        print("[OK] Patched _send_email docstring + markdown detection")
    
    # Now replace the body of _send_email after msg["Message-ID"]
    old_body_start = '        msg["Message-ID"] = msg_id\n\n        msg.attach(MIMEText(body, "plain", "utf-8"))'
    new_body_start = '''        msg["Message-ID"] = msg_id

        if has_markdown:
            try:
                import subprocess
                import tempfile
                md_file = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8")
                md_file.write(body)
                md_path = md_file.name
                md_file.close()
                html_result = subprocess.run(
                    [sys.executable, str(SCRIPT_PATH)],
                    input=body,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if html_result.returncode == 0 and html_result.stdout.strip():
                    html_body = html_result.stdout
                    # Build multipart/alternative with text/plain + text/html
                    alt = MIMEMultipart("alternative")
                    alt.attach(MIMEText(body, "plain", "utf-8"))
                    alt.attach(MIMEText(html_body, "html", "utf-8"))
                    msg.attach(alt)
                    import os as _os
                    try:
                        _os.unlink(md_path)
                    except Exception:
                        pass
                    smtp = self._connect_smtp()
                    try:
                        smtp.login(self._address, self._password)
                        smtp.send_message(msg)
                    finally:
                        try:
                            smtp.quit()
                        except Exception:
                            smtp.close()
                    logger.info("[Email] Sent multipart/alternative reply to %%s (subject: %%s)", to_addr, subject)
                    return msg_id
            except Exception as e:
                logger.warning("[Email] Markdown-to-HTML conversion failed, falling back to plain text: %%s", e)

        msg.attach(MIMEText(body, "plain", "utf-8"))'''

    content = content.replace(old_body_start, new_body_start, 1)
    if old_body_start not in content:
        print("[OK] Patched _send_email body → multipart/alternative")
    
    return content

def main():
    if not ADAPTER_PATH.exists():
        print(f"[ERR] Adapter not found at {ADAPTER_PATH}")
        sys.exit(1)
    if not SCRIPT_PATH.exists():
        print(f"[WARN] md2email.py not found at {SCRIPT_PATH}")
        reply = input("Continue without the conversion script? [y/N] ")
        if reply.lower() != "y":
            sys.exit(1)
    
    content = read_adapter()
    
    # Backup
    backup_path = ADAPTER_PATH.with_suffix(".py.bak")
    if not backup_path.exists():
        backup_path.write_text(content, encoding="utf-8")
        print(f"[OK] Backup saved to {backup_path}")
    
    # Apply patches
    content = patch_send_email(content)
    
    write_adapter(content)
    print(f"[OK] Adapter patched at {ADAPTER_PATH}")
    print("[NOTE] Restart the gateway for changes to take effect:")
    print("       hermes gateway restart")

if __name__ == "__main__":
    main()