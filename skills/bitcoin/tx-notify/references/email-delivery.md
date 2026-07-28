# Delivery email — tx-notify

Trois méthodes testées pour envoyer des emails depuis l'agent. La plus fiable est Himalaya template send.

## Méthode 1 : SMTP direct via smtplib (dans le script bash)

Utilisée dans `tx-watch.sh` — appel automatique à la confirmation. Pas de dépendance externe, tout est dans la stdlib Python.

```python
import smtplib
from email.mime.text import MIMEText

msg = MIMEText(body)
msg['Subject'] = subject
msg['From'] = 'wizard-u3@hxmt.xyz'
msg['To'] = 'galoisfield2718@gmail.com'

with smtplib.SMTP('smtp.mail.ovh.net', 587) as s:
    s.starttls()
    s.login('wizard-u3@hxmt.xyz', 'NazjrMzLruXk5EyA')
    s.send_message(msg)
```

**Problème de délivrabilité :** Gmail peut bloquer silencieusement les emails venant du SMTP OVH si SPF/DKIM ne sont pas configurés. L'email est "queued" (confirmé par OVH) mais n'arrive jamais. Vérifier :
- Les spams Gmail
- `INBOX.Sent` sur IMAP OVH pour confirmer l'envoi
- Utiliser Himalaya (méthode 2) qui semble mieux passer

## Méthode 2 : Himalaya template send (recommandé pour fiabilité)

Himalaya a bien fonctionné après plusieurs essais. Syntaxe exacte :

```bash
cat << EOF | ~/.local/bin/himalaya template send -a wizard
From: wizard-u3@hxmt.xyz
To: galoisfield2718@gmail.com
Subject: 🧙 Ton sujet ici

Corps du message en texte simple.

--
Signature
EOF
```

**Points critiques :**
- Le `From:` est OBLIGATOIRE — Himalaya refuse "cannot send message without a sender" sans ça
- Le flag `-a wizard` spécifie le compte (défini dans la config himalaya)
- Le corps est du texte pur — pas de markdown rendu
- L'objet supporte les emojis (UTF-8)

## Méthode 3 : Himalaya template send avec pièce jointe

Utilisation du MML (MIME Markup Language) pour joindre un fichier :

```bash
cat << 'MML' > /tmp/message.mml
From: wizard-u3@hxmt.xyz
To: galoisfield2718@gmail.com
Subject: 🧙 Schéma avec pièce jointe

Corps du message.

<#part type=application/octet-stream filename=mon-fichier.html disposition=attachment>
MML

# Ajouter le contenu binaire/texte
cat /home/hermes/mon-fichier.html >> /tmp/message.mml

# Fermer la pièce jointe (NÉCESSAIRE)
echo '<#/part>' >> /tmp/message.mml

# Envoyer
~/.local/bin/himalaya template send -a wizard < /tmp/message.mml
```

**Points critiques :**
1. La directive `<#part>` doit être sur sa propre ligne, **avant** le contenu du fichier
2. `<#/part>` de fermeture OBLIGATOIRE après le contenu
3. Le contenu du fichier suit immédiatement `<#part>` (pas de ligne vide)
4. Le fichier peut être du texte brut ou du binaire — Himalaya encode
5. `disposition=attachment` pour forcer le téléchargement (vs `disposition=inline`)

## Vérification IMAP (confirmer que l'email est parti)

```python
import imaplib, email
mail = imaplib.IMAP4_SSL('imap.mail.ovh.net', 993)
mail.login('wizard-u3@hxmt.xyz', 'NazjrMzLruXk5EyA')
mail.select('INBOX.Sent')
status, msgs = mail.search(None, 'ALL')
for i in msgs[0].split()[-3:]:
    status, data = mail.fetch(i, '(BODY.PEEK[HEADER.FIELDS (SUBJECT DATE TO)])')
    msg = email.message_from_bytes(data[0][1])
    print(f"{msg['Date'][:25]} — {msg['Subject']} → {msg['To']}")
mail.logout()
```

## Canal de livraison : Telegram vs Email

Dans Hermes, `terminal()` avec `notify_on_complete=True` livre TOUJOURS vers le chat d'origine (Telegram). Il n'y a pas de paramètre `deliver` sur `terminal()`.

Pour envoyer UNIQUEMENT par email (sans Telegram), deux options :
1. **Pas de `notify_on_complete`** — le script tourne en background, envoie l'email tout seul via `send_email()`, et exit. Zéro notif Telegram.
2. **Les deux** — `notify_on_complete=True` pour Telegram + `send_email()` dans le script pour l'email. Les deux canaux fonctionnent en parallèle.

La solution (1) est plus propre quand on veut email-only : pas de dépendance au runtime Hermes pour la livraison, le script est autonome.

## Credentials

Stockés dans `~/.hermes/.env` :
```
EMAIL_ADDRESS=wizard-u3@hxmt.xyz
EMAIL_PASSWORD=NazjrMzLruXk5EyA
EMAIL_IMAP_HOST=imap.mail.ovh.net
EMAIL_IMAP_PORT=993
EMAIL_SMTP_HOST=smtp.mail.ovh.net
EMAIL_SMTP_PORT=587
EMAIL_HOME_ADDRESS=galoisfield2718@gmail.com
```