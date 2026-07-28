#!/usr/bin/env bash
# setup_himalaya.sh — Configure himalaya for the markdown-to-email skill
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Setting up himalaya for markdown-to-email skill ==="

# 1. Install himalaya if not present
if ! command -v himalaya &>/dev/null && ! ~/.local/bin/himalaya --version &>/dev/null 2>&1; then
    echo "[STEP 1/4] Installing himalaya CLI..."
    curl -fsSL https://raw.githubusercontent.com/pimalaya/himalaya/master/install.sh \
        | PREFIX=~/.local sh
    echo "[OK] himalaya installed"
else
    echo "[OK] himalaya already installed: $(~/.local/bin/himalaya --version 2>/dev/null || himalaya --version 2>/dev/null)"
fi

export PATH="$HOME/.local/bin:$PATH"

# 2. Read SMTP/IMAP credentials from .env if available
ENV_FILE="$HOME/.hermes/.env"
if [ -f "$ENV_FILE" ]; then
    echo "[STEP 2/4] Reading email credentials from $ENV_FILE"
    set -a
    source "$ENV_FILE"
    set +a
fi

# Validate required vars
: "${EMAIL_ADDRESS:?EMAIL_ADDRESS not set in .env}"
: "${EMAIL_PASSWORD:?EMAIL_PASSWORD not set in .env}"
: "${EMAIL_SMTP_HOST:?EMAIL_SMTP_HOST not set in .env}"
: "${EMAIL_IMAP_HOST:?EMAIL_IMAP_HOST not set in .env}"

# 3. Create password file
echo "[STEP 3/4] Creating password file at ~/.config/himalaya/email_password"
mkdir -p ~/.config/himalaya
echo -n "$EMAIL_PASSWORD" > ~/.config/himalaya/email_password
chmod 600 ~/.config/himalaya/email_password
echo "[OK] Password file created"

# 4. Generate config
echo "[STEP 4/4] Generating ~/.config/himalaya/config.toml"

DISPLAY_NAME="${EMAIL_DISPLAY_NAME:-Bitcoin Wizard}"

cat > ~/.config/himalaya/config.toml << HERMESEOF
[accounts.wizard]
email = "${EMAIL_ADDRESS}"
display-name = "${DISPLAY_NAME}"
default = true

backend.type = "imap"
backend.host = "${EMAIL_IMAP_HOST}"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "${EMAIL_ADDRESS}"
backend.auth.type = "password"
backend.auth.cmd = "cat ${HOME}/.config/himalaya/email_password"

message.send.backend.type = "smtp"
message.send.backend.host = "${EMAIL_SMTP_HOST}"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "${EMAIL_ADDRESS}"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "cat ${HOME}/.config/himalaya/email_password"

folder.aliases.inbox = "INBOX"
folder.aliases.sent = "Sent"
folder.aliases.drafts = "Drafts"
folder.aliases.trash = "Trash"
HERMESEOF

echo "[OK] Config written"

# 5. Create standard IMAP folders if they don't exist
echo "[STEP 5] Creating standard IMAP folders on server..."
python3 -c "
import imaplib, ssl
try:
    ctx = ssl.create_default_context()
    imap = imaplib.IMAP4_SSL('${EMAIL_IMAP_HOST}', 993, timeout=15)
    imap.login('${EMAIL_ADDRESS}', '${EMAIL_PASSWORD}')
    for f in ['Sent', 'Drafts', 'Trash', 'Junk']:
        imap.create(f)
    imap.logout()
    print('[OK] IMAP folders created')
except Exception as e:
    print(f'[WARN] Could not create all folders: {e}')
"

# 6. Test
echo "[STEP 6/6] Testing himalaya connection..."
if himalaya folder list &>/dev/null; then
    echo "[OK] himalaya connected successfully"
else
    echo "[WARN] himalaya folder list failed — check credentials"
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "To test:"
echo "  MD_CONTENT=\$(cat << 'HERMD'"
echo "  # Test"
echo "  **Hello** from the Wizard"
echo "  HERMD"
echo "  )"
echo "  HTML_CONTENT=\$(python3 ${SCRIPT_DIR}/md2email.py <<< \"\$MD_CONTENT\")"
echo "  {"
echo "    echo 'To: <recipient>@example.com'"
echo "    echo 'Subject: Test HTML Email'"
echo "    echo ''"
echo "    echo '<#multipart type=alternative>'"
echo "    echo \"\$MD_CONTENT\""
echo "    echo ''"
echo "    echo '<#part type=text/html>'"
echo "    echo \"\$HTML_CONTENT\""
echo "    echo '<#/multipart>'"
echo "  } | himalaya template send"