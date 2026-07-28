#!/usr/bin/env python3
"""
send_scheduled_email.py — Envoie un email HTML avec piece jointe SVG via SMTP direct.

Utilise smtplib (stdlib) — aucune dependance externe.
Lit les credentials depuis le .env de Hermes.

Usage:
    python3 send_scheduled_email.py
"""

import os
import re
import smtplib
import ssl
import subprocess
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.utils import formatdate
from email import encoders
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────

HERMES_HOME = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")))
ENV_FILE = HERMES_HOME / ".env"
SKILL_DIR = HERMES_HOME / "skills" / "email" / "markdown-to-email"
SCHEDULED_DIR = HERMES_HOME / "scheduled"

# ── Read credentials from .env ─────────────────────────────────────────────

def load_env():
    """Charge les variables depuis le .env de Hermes."""
    if not ENV_FILE.exists():
        print(f"[ERREUR] Fichier .env introuvable : {ENV_FILE}", file=sys.stderr)
        sys.exit(1)
    
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())


def get_cred(key):
    val = os.getenv(key, "").strip()
    if not val:
        print(f"[ERREUR] {key} non defini dans .env", file=sys.stderr)
        sys.exit(1)
    return val


# ── Markdown to HTML ──────────────────────────────────────────────────────

def md_to_html(md_text):
    """Convertit le markdown en HTML via md2email.py."""
    script = SKILL_DIR / "scripts" / "md2email.py"
    if not script.exists():
        print(f"[ERREUR] md2email.py introuvable : {script}", file=sys.stderr)
        return None
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            input=md_text,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
        print(f"[WARN] md2email.py echec (exit={result.returncode})", file=sys.stderr)
    except Exception as e:
        print(f"[WARN] md2email.py erreur : {e}", file=sys.stderr)
    return None


# ── Build email ────────────────────────────────────────────────────────────

def build_email(from_addr, to_addrs, cc_addrs, subject, md_body, svg_path):
    """Construit un MIME multipart/alternative + piece jointe SVG."""
    msg = MIMEMultipart("mixed")
    msg["From"] = f"Bitcoin Wizard <{from_addr}>"
    msg["To"] = ", ".join(to_addrs)
    msg["Cc"] = ", ".join(cc_addrs)
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = f"<hermesdeck-{datetime.now().strftime('%Y%m%d%H%M%S')}@{from_addr.split('@')[-1]}>"

    # Part alternative (text/plain + text/html)
    alt = MIMEMultipart("alternative")
    
    # Texte brut
    alt.attach(MIMEText(md_body, "plain", "utf-8"))
    
    # HTML
    html = md_to_html(md_body)
    if html:
        alt.attach(MIMEText(html, "html", "utf-8"))
    
    msg.attach(alt)

    # Piece jointe SVG
    if svg_path and Path(svg_path).exists():
        with open(svg_path, "rb") as f:
            svg_data = f.read()
        svg_part = MIMEImage(
            svg_data,
            _subtype="svg+xml",
            name="hermesdeck_banner.svg",
        )
        svg_part.add_header(
            "Content-Disposition",
            "attachment; filename=hermesdeck_banner.svg",
        )
        svg_part.add_header("Content-ID", "<hermesdeck-banner>")
        msg.attach(svg_part)

    return msg


# ── Send via SMTP ──────────────────────────────────────────────────────────

def send_email(msg, smtp_host, smtp_port, smtp_user, smtp_pass, all_recipients):
    """Envoie l'email via SMTP avec STARTTLS."""
    ctx = ssl.create_default_context()
    try:
        smtp = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
        smtp.ehlo()
        smtp.starttls(context=ctx)
        smtp.ehlo()
        smtp.login(smtp_user, smtp_pass)
        smtp.sendmail(smtp_user, all_recipients, msg.as_string())
        smtp.quit()
        print(f"[OK] Email envoye a {len(all_recipients)} destinataire(s)")
        return True
    except Exception as e:
        print(f"[ERREUR] Echec SMTP : {e}", file=sys.stderr)
        return False


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    load_env()

    # Credentials
    from_addr = get_cred("EMAIL_ADDRESS")
    smtp_host = get_cred("EMAIL_SMTP_HOST")
    smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    smtp_pass = get_cred("EMAIL_PASSWORD")

    # Destinataires
    to_addrs = ["nftgang1618@gmail.com", "dorian.espagne@gmail.com"]
    cc_addrs = ["galoisfield2718@gmail.com"]
    all_recipients = to_addrs + cc_addrs

    subject = "Automatisation des taches repetitives par Workflow Agent & Harnais agentique"

    # Contenu markdown
    md_content = """# Automatisation des taches repetitives par Workflow Agent & Harnais agentique

Bonjour,

Je vous contacte dans le cadre d'une reflexion sur l'automatisation intelligente des taches repetitives — un sujet qui concerne autant la gestion de communautes Web3 que les processus metier classiques.

## Le constat

Chaque jour, des heures sont perdues sur des taches qui pourraient etre executees par un agent logiciel : surveillance de smart contracts, moderation de communautes, generation de rapports, veille concurrentielle, qualification de leads, suivi de projets.

## La solution : Workflow Agents

Un **Workflow Agent** est un programme AI autonome qui :

- Execute des taches selon un plan defini (un "workflow")
- S'adapte aux resultats intermediaires
- Vous notifie uniquement quand une decision humaine est necessaire
- Fonctionne **24h/24 et 7j/7** sans supervision humaine

### Exemples concrets

**Pour le Web3 :** Un agent qui surveille les ventes d'une collection NFT, analyse les tendances du marche, genere un rapport quotidien, et alerte en cas d'activite suspecte sur un smart contract.

**Pour le business :** Un agent qui qualifie les leads entrants, met a jour un CRM, programme des relances automatiques, et prepare un briefing hebdomadaire.

## Le Harnais Agentique

Quand on coordonne plusieurs agents specialises, on obtient un **harnais agentique** — une equipe virtuelle qui travaille 24h/24 :

- **Agent de veille** — surveille vos sources (blockchain, reseaux, emails)
- **Agent d'analyse** — synthetise l'information et detecte les tendances
- **Agent de redaction** — prepare les rapports et les communications
- **Agent de decision** — escalade les cas critiques et propose des actions

Le tout orchestre, documente, et modifiable sans competence technique.

Voici un schema de l'architecture type :

![Architecture HermesDeck](cid:hermesdeck-banner)

## Pourquoi maintenant ?

Les modeles de langage (LLM) ont atteint un niveau de fiabilite qui rend l'automatisation agentique viable pour la premiere fois. La combinaison de :

- **LLM** pour la comprehension et la generation de texte
- **Outils** pour interagir avec le monde (API, bases de donnees, emails)
- **Orchestration** pour coordonner plusieurs agents

...permet de deleguer des chaines de taches completes a un systeme autonome.

## Prochaine etape

Je propose un echange de 20 minutes pour :

1. Identifier vos taches repetitives les plus chronophages
2. Definir un workflow agentique sur mesure
3. Vous montrer une demonstration en conditions reelles

**Mes disponibilites :**

- Lundi 14 juillet a 14h00 (UTC+2)
- Mardi 15 juillet a 10h00 (UTC+2)
- Jeudi 17 juillet a 16h00 (UTC+2)

Un simple retour sur ce fil suffit pour confirmer un creneau — je vous enverrai le lien de connexion.

---

*Bitcoin Wizard*  
*Agent Hermes — Nous Research*
"""

    # Chemin du SVG
    svg_path = SCHEDULED_DIR / "hermesdeck_banner.svg"

    # Construction et envoi
    print(f"[ENVOI] {datetime.now().isoformat()}")
    print(f"[INFO] De : {from_addr}")
    print(f"[INFO] A  : {', '.join(to_addrs)}")
    print(f"[INFO] Cc : {', '.join(cc_addrs)}")
    print(f"[INFO] Sujet : {subject}")

    msg = build_email(from_addr, to_addrs, cc_addrs, subject, md_content, str(svg_path))
    success = send_email(msg, smtp_host, smtp_port, from_addr, smtp_pass, all_recipients)

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()