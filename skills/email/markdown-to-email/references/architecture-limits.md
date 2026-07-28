# Email Architecture Limits — What Does NOT Work

This document captures the boundaries of the Hermes built-in email gateway,
learned through trial and error, so future sessions do not repeat the same
dead ends.

## The Built-in Gateway Sends text/plain Only

The `EmailAdapter._send_email()` method in
`plugins/platforms/email/adapter.py` builds a MIME message with
`MIMEText(body, "plain", "utf-8")`. There is no HTML alternative part.

The adapter file is owned by root and lives under `/usr/local/lib/`.
Without sudo access, it cannot be modified. There is no user-level plugin
hook for intercepting outgoing email messages — the plugin system has
`on_session_end` hooks but no `on_email_send` hook.

## MEDIA: Tag Limits

The `MEDIA:/path/to/file.html` tag in the agent's response:

1. **Is NOT processed by the email adapter** — the gateway extracts MEDIA
   tags before calling `send()`. The HTML file is sent as a *separate*
   `application/octet-stream` attachment via `send_document()`, not
   merged into the email body.

2. **Is NOT auto-appended** — the auto-append mechanism in
   `gateway/run.py` only handles specific producer tools (TTS,
   image_generate), not generic MEDIA tags in agent prose.

3. **The .html extension IS supported** by `MEDIA_DELIVERY_EXTS` in
   `gateway/platforms/base.py` (line 1448). But it's treated as a
   deliverable document, not as an alternative body part.

## Why a User Plugin Won't Work

The `~/.hermes/plugins/` path supports user plugins. However:

- Standalone user plugins require explicit `plugins.enabled` in config.yaml
- The email adapter is loaded lazily (deferred platform), so it may not
  be importable at `register()` time
- There is no `on_email_send` hook in `VALID_HOOKS`
- Monkey-patching the adapter class works only if the plugin is
  configured and loaded before the first email send

## The Working Solution: Himalaya MML Multipart/Alternative

Bypass the built-in gateway entirely for outgoing messages:

1. Install `himalaya` CLI (Rust binary, no dependencies)
2. Configure it with the same SMTP credentials (password file approach)
3. Build a `multipart/alternative` MIME message using MML syntax
4. Pipe to `himalaya template send`

The HTML renders inline in Gmail, Fastmail, Outlook, Thunderbird — no
file attachments needed.