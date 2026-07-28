# Himalaya MML Multipart Workflow

Combine the `markdown-to-email` skill (produces HTML) with himalaya (SMTP delivery)
to send multipart/alternative emails with a plain text fallback and inline HTML rendering.

**New to this skill?** The SKILL.md contains the full workflow.
This reference covers threaded replies and details.

## Threaded Reply

When replying, use `In-Reply-To` and `References` headers for proper threading:

```bash
MD_CONTENT=$(cat << 'HERMD'
# Re: Original Subject

**bold** reply text here.
HERMD
)

{
  echo "From: wizard-u3@hxmt.xyz"
  echo "To: original-sender@example.com"
  echo "Subject: Re: Original Subject"
  echo "In-Reply-To: <original-message-id@server>"
  echo "References: <original-message-id@server>"
  echo ""
  echo '<#multipart type=alternative>'
  echo "$MD_CONTENT"
  echo ''
  echo '<#part type=text/html>'
  python3 /home/hermes/.hermes/skills/email/markdown-to-email/scripts/md2email.py <<< "$MD_CONTENT"
  echo '<#/multipart>'
} | himalaya template send
```

## Comparison: MEDIA vs MML

| Method | Pros | Cons |
|---|---|---|
| MEDIA attachment in built-in gateway | Simple, no extra CLI | Sent as attachment, not inline; always text/plain body |
| MML multipart/alternative via himalaya | Renders inline with rich HTML; text fallback | Requires himalaya CLI + config |

## Requirements

- himalaya CLI installed and configured (same SMTP credentials as the gateway)
- Password file at `~/.config/himalaya/email_password` (mode 600)
- IMAP Sent folder exists (see `references/imap-folder-creation.md`)

## See Also

- `references/architecture-limits.md` — why the built-in gateway cannot do this
- `references/imap-folder-creation.md` — IMAP folder setup for sent-message saving