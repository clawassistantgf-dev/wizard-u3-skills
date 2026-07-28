# DNS Deliverability Diagnostics

When SMTP confirms "OK" but the recipient never receives the email, the
problem is almost always on the **receiving server's authentication check**
(SPF/DKIM/DMARC). Gmail is the strictest common recipient.

## Query DNS Records

Use Google's DNS-over-HTTPS API (no dig/host/nslookup needed):

### MX (mail servers)

```bash
curl -s "https://dns.google/resolve?name=DOMAIN&type=MX"
```

### SPF (authorized senders)

```bash
curl -s "https://dns.google/resolve?name=DOMAIN&type=TXT"
```

Look for `v=spf1 ...`. Common values:
- `include:mx.ovh.net -all` — only OVH MX servers, hard fail for others
- `include:_spf.google.com ~all` — Google Workspace, soft fail
- `?all` — neutral (no policy)

### DKIM (signing key)

OVH typically uses `ovh._domainkey`, `s1._domainkey`, or `s2._domainkey`.

```bash
for sel in s1 s2 s2048 s1024 ovh default; do
  curl -s "https://dns.google/resolve?name=${sel}._domainkey.DOMAIN&type=TXT"
done
```

A Status: 0 response with an Answer containing a `v=DKIM1; p=...` record
means DKIM is active. Status: 3 (NXDOMAIN) means no DKIM record exists.

### DMARC (reporting/rejection policy)

```bash
curl -s "https://dns.google/resolve?name=_dmarc.DOMAIN&type=TXT"
```

- `p=none` — monitoring only, no rejection
- `p=quarantine` — send to spam
- `p=reject` — reject outright

## Interpret the JSON

| Field | Meaning |
|---|---|
| `Status: 0` | Record found (Answer present) |
| `Status: 3` | NXDOMAIN — record does not exist |
| `Answer[].data` | The actual TXT/MX record value |
| `Authority[].data` | SOA record (domain exists but subrecord does not) |

## Common Problems

### Problem: SPF hard fail (-all) but IP not authorized

The sending SMTP server's IP is not in the SPF include list. Gmail
rejects the email. Fix: add the IP or include the provider's SPF include.

### Problem: No DKIM record

Gmail silently drops emails without DKIM, even if SPF passes. Fix:
generate a DKIM key pair in your hosting control panel and add the
public key as a TXT record at `SELECTOR._domainkey.DOMAIN`.

### Problem: DMARC p=reject but SPF/DKIM not aligned

Gmail enforces DMARC alignment: the domain in the From header must match
the domain authenticated by SPF or DKIM. Fix: ensure the From domain
matches the authenticated sending domain.

## OVH-Specific

OVH provisions email but does not always auto-configure DKIM. To enable:
1. Log into OVH Control Panel -> Web Cloud -> Domain names
2. Select your domain -> Emails -> DKIM
3. Click "Generate" (this creates the DNS record on OVH's DNS servers)
4. Wait up to 24 hours for propagation
5. Verify with the curl commands above

OVH SPF include target: `include:mx.ovh.com` — this covers both incoming
MX and outgoing SMTP servers on the OVH infrastructure.

## Test Delivery After Fixing DNS

```python
import smtplib, ssl
from email.mime.text import MIMEText
from email.utils import formatdate

ctx = ssl.create_default_context()
smtp = smtplib.SMTP("smtp.mail.ovh.net", 587, timeout=30)
smtp.ehlo()
smtp.starttls(context=ctx)
smtp.ehlo()
smtp.login("user@domain.com", "password")

msg = MIMEText("DKIM delivery test", "plain", "utf-8")
msg["From"] = "user@domain.com"
msg["To"] = "testrecipient@gmail.com"
msg["Subject"] = "DKIM Test $(date)"
smtp.sendmail("user@domain.com", ["testrecipient@gmail.com"], msg.as_string())
smtp.quit()
print("Sent — check spam folder on recipient")
```