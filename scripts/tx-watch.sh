#!/usr/bin/env bash
# tx-watch.sh — Bitcoin transaction watcher
# 
# Modes :
#   tx-watch.sh <txid>            → single check (watchdog cron)
#   tx-watch.sh --watch <txid>    → auto-poll toutes les 10s
#   tx-watch.sh --watch --interval 30 <txid>
#
# Modular : ajoute des features dans la section dédiée

set -euo pipefail

# === Configuration par défaut ===
MEMPOOL_BASE="${MEMPOOL_URL:-https://mempool.space}"
POLL_INTERVAL=10
MAX_POLLS=0  # 0 = infini (--watch sans timeout)

# === Fonctions modulaires (ajoutez-en ici) ===

check_confirmation() {
    local txid="$1"
    local response
    response=$(curl -s --max-time 10 --retry 2 --retry-delay 1 \
        "${MEMPOOL_BASE}/api/tx/${txid}" 2>/dev/null) || { echo "0"; return 1; }
    
    echo "$response" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    bh = d.get('status', {}).get('block_height', 0) or 0
    print(bh)
except:
    print(0)
" 2>/dev/null || echo "0"
}

get_tx_info() {
    local txid="$1"
    curl -s --max-time 10 --retry 2 --retry-delay 1 \
        "${MEMPOOL_BASE}/api/tx/${txid}" 2>/dev/null
}

format_notification() {
    local txid="$1"
    local tx_json="$2"
    
    # Sauver dans un fichier temporaire pour éviter les problèmes d'interpolation shell
    local tmpfile
    tmpfile=$(mktemp /tmp/tx-notify-XXXXXX.json)
    echo "$tx_json" > "$tmpfile"
    
    python3 -c "
import sys, json

with open('${tmpfile}') as f:
    d = json.load(f)

txid = '''${txid}'''

value = d.get('value', 0) or 0
fee = d.get('fee', 0) or 0
block = d.get('status', {}).get('block_height', 0)
n_inputs = len(d.get('vin', []))
n_outputs = len(d.get('vout', []))
btc_value = value / 1e8
btc_fee = fee / 1e8
is_coinbase = len(d.get('vin', [])) > 0 and d['vin'][0].get('is_coinbase', False)

lines = []
lines.append('')
lines.append('═' * 42)
lines.append('')
if is_coinbase:
    lines.append(f'⛏️  COINBASE — Block {block}')
lines.append(f'✅ TX CONFIRMÉE')
lines.append('')
lines.append(f'📍 TXID : {txid[:16]}...{txid[-8:]}')
lines.append(f'📦 Block: {block:,}'.replace(',', ' '))
if btc_value > 0:
    lines.append(f'💰 Value : {btc_value:.8f} BTC ({btc_value:.2f} BTC)')
if btc_fee > 0:
    lines.append(f'⛽ Fee   : {btc_fee:.8f} BTC')
lines.append(f'🔗 I/O   : {n_inputs} → {n_outputs}')
lines.append('')
lines.append(f'🔗 https://mempool.space/tx/{txid}')
lines.append('')
print(chr(10).join(lines))
" 2>/dev/null
}

# === Future features : ajouter ici ===
#
# Exemple : notifier le prix BTC si variation > X%
# check_price_move(threshold_pct) { ... echo "⚠️ BTC +3.2% en 1h" }

# Envoie un email via SMTP OVH (config .env)
send_email() {
    local subject="$1"
    local body="$2"
    local from="wizard-u3@hxmt.xyz"
    local to="galoisfield2718@gmail.com"
    
    python3 -c "
import smtplib
from email.mime.text import MIMEText

msg = MIMEText('''${body}''')
msg['Subject'] = '${subject}'
msg['From'] = '${from}'
msg['To'] = '${to}'

try:
    with smtplib.SMTP('smtp.mail.ovh.net', 587) as s:
        s.starttls()
        s.login('${from}', 'NazjrMzLruXk5EyA')
        s.send_message(msg)
    print('✅ Email sent')
except Exception as e:
    print(f'❌ Email failed: {e}')
" 2>/dev/null
}
#
# Exemple : surveiller une adresse
# check_address_txs(address) { ... echo "📥 Nouvelle tx reçue" }
#
# Exemple : notifier les frais moyens du mempool
# check_mempool_fees() { ... echo "⛽ Frais moyens: 8 sat/vB" }

# === Watchdog single check (mode cron) ===
watchdog_check() {
    local txid="$1"
    local block_height
    block_height=$(check_confirmation "$txid")
    
    if [ "$block_height" -gt 0 ]; then
        local tx_info
        tx_info=$(get_tx_info "$txid")
        format_notification "$txid" "$tx_info"
        return 0
    fi
    # Silence = pas de livraison
    return 0
}

# === Auto-poll mode (--watch) ===
auto_poll() {
    local txid="$1"
    local interval="$2"
    local max="$3"
    
    local count=0
    while true; do
        local block_height
        block_height=$(check_confirmation "$txid") || true
        
        if [ -n "$block_height" ] && [ "$block_height" -gt 0 ]; then
            local tx_info
            tx_info=$(get_tx_info "$txid")
            local msg
            msg=$(format_notification "$txid" "$tx_info")
            echo "$msg"
            send_email "✅ BTC Confirmée ${txid:0:16}..." "$msg"
            return 0
        fi
        
        count=$((count + 1))
        # Si max > 0, check timeout
        if [ "$max" -gt 0 ] && [ "$count" -ge "$max" ]; then
            echo "⏰ Timeout après ${max} polls (${interval}s d'intervalle)"
            return 1
        fi
        sleep "$interval"
    done
}

# === Main ===
main() {
    local txid=""
    local mode="watchdog"
    local interval="$POLL_INTERVAL"
    local max="$MAX_POLLS"
    
    # Parse arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            --watch|-w)
                mode="auto_poll"
                shift
                ;;
            --interval|-i)
                interval="$2"
                shift 2
                ;;
            --max|-m)
                max="$2"
                shift 2
                ;;
            --help|-h)
                echo "Usage:"
                echo "  tx-watch.sh <txid>                   # single check (watchdog)"
                echo "  tx-watch.sh --watch <txid>           # poll toutes les ${interval}s"
                echo "  tx-watch.sh --watch -i 30 <txid>     # poll toutes les 30s"
                echo "  MEMPOOL_URL=http://localhost:3000 tx-watch.sh <txid>  # custom mempool"
                exit 0
                ;;
            *)
                if [ -z "$txid" ]; then
                    txid="$1"
                fi
                shift
                ;;
        esac
    done
    
    if [ -z "$txid" ]; then
        echo "❌ Usage: tx-watch.sh [--watch] [--interval N] <txid>"
        exit 1
    fi
    
    if ! [[ "$txid" =~ ^[a-fA-F0-9]{64}$ ]]; then
        echo "❌ TXID invalide : doit être 64 caractères hex"
        exit 1
    fi
    
    case "$mode" in
        auto_poll)
            auto_poll "$txid" "$interval" "$max"
            ;;
        watchdog)
            watchdog_check "$txid"
            ;;
    esac
}

main "$@"