# IMAP Folder Creation for himalaya

Many email providers (OVH, Hetzner, Ionos, and other shared/enterprise
hosts) start with ONLY an INBOX folder. Standard folders like Sent,
Drafts, and Trash must be created manually. Without them, `himalaya
template send` will succeed via SMTP but then fail with:

```
Error: cannot add IMAP message
  stream error
  unexpected tag in command completion result
```

The email IS delivered — the error comes from the IMAP save-to-Sent
folder, not from SMTP. Exit code will be 1 despite successful delivery.

## Create Folders via Python (no extra tools)

```python
import imaplib
import ssl

ctx = ssl.create_default_context()
imap = imaplib.IMAP4_SSL("imap.example.com", 993, timeout=15)
imap.login("user@example.com", "password")

for folder in ["Sent", "Drafts", "Trash", "Junk"]:
    imap.create(folder)

imap.logout()
```

## Create Folders via himalaya

If himalaya is already configured:

```bash
himalaya folder create "Sent"
himalaya folder create "Drafts"
himalaya folder create "Trash"
```

## Verify

```bash
himalaya folder list
# Should show: INBOX, Sent, Drafts, Trash, Junk
```

Then test SMTP + IMAP save together:

```bash
echo -e "From: user@example.com\nTo: you@example.com\nSubject: Test\n\nHello" \
  | himalaya template send
```

## Gmail Note

Gmail uses `[Gmail]/Sent Mail` instead of `Sent`. Configure the alias:

```toml
folder.aliases.sent = "[Gmail]/Sent Mail"
folder.aliases.drafts = "[Gmail]/Drafts"
folder.aliases.trash = "[Gmail]/Trash"
```

## When to Create Folders

- **First-time setup** — always create them after configuring himalaya
- **Server migration** — if the hosting provider changed, check folders
- **Account reset** — if the mailbox was reset/re-provisioned