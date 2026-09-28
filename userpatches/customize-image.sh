#!/bin/bash
set -euo pipefail

SRC="/tmp/overlay/opt/pisowifi-source"
ENV_FILE="/tmp/overlay/etc/pisowifi/build.env"

if [[ ! -d "$SRC" ]]; then
  echo "ERROR: PisoWiFi source overlay missing: $SRC" >&2
  exit 1
fi

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

install -d /opt/pisowifi /etc/pisowifi /var/lib/pisowifi

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  python3 python3-venv python3-pip python3-libgpiod gpiod \
  hostapd dnsmasq nftables iproute2 iw sqlite3

cp -a "$SRC/portal" "$SRC/coin" "$SRC/scripts" /opt/pisowifi/
cp "$SRC/config/plans.json" /etc/pisowifi/plans.json
cp "$SRC/config/pisowifi.env.example" /etc/pisowifi/pisowifi.env
cp "$SRC/config/hostapd.conf" /etc/hostapd/hostapd.conf
cp "$SRC/config/dnsmasq.conf" /etc/dnsmasq.d/pisowifi.conf
cp "$SRC/config/nftables.conf" /etc/nftables.conf
cp "$SRC/systemd/"*.service "$SRC/systemd/"*.timer /etc/systemd/system/
cp "$SRC/scripts/tc_setup.py" /usr/local/sbin/pisowifi-tc
chmod 0755 /usr/local/sbin/pisowifi-tc

python3 -m venv --system-site-packages /opt/pisowifi/venv
/opt/pisowifi/venv/bin/pip install --no-cache-dir Flask==3.1.0 Werkzeug==3.1.3

WIFI_INTERFACE="${PISOWIFI_WIFI_INTERFACE:-wlan0}"
WAN_INTERFACE="${PISOWIFI_WAN_INTERFACE:-eth0}"
SSID="${PISOWIFI_SSID:-PisoWiFi}"
WIFI_PASSWORD="${PISOWIFI_WIFI_PASSWORD:-change-me-12345}"
ADMIN_PASSWORD="${PISOWIFI_ADMIN_PASSWORD:-change-me-now}"
GPIO_CHIP="${PISOWIFI_GPIO_CHIP:-/dev/gpiochip0}"
GPIO_LINE="${PISOWIFI_GPIO_LINE:-6}"

python3 - "$WIFI_INTERFACE" "$WAN_INTERFACE" "$SSID" "$WIFI_PASSWORD" "$ADMIN_PASSWORD" "$GPIO_CHIP" "$GPIO_LINE" <<'PY'
from pathlib import Path
import secrets
import sys

wifi, wan, ssid, wifi_pw, admin_pw, gpio_chip, gpio_line = sys.argv[1:]

env = Path('/etc/pisowifi/pisowifi.env')
text = env.read_text()
replacements = {
    'WIFI_INTERFACE': wifi,
    'WAN_INTERFACE': wan,
    'WIFI_SSID': ssid,
    'WIFI_PASSWORD': wifi_pw,
    'ADMIN_PASSWORD': admin_pw,
    'APP_SECRET': secrets.token_urlsafe(32),
    'COIN_GPIO_CHIP': gpio_chip,
    'COIN_GPIO_LINE': gpio_line,
}
lines = []
seen = set()
for line in text.splitlines():
    if '=' in line and not line.startswith('#'):
        key = line.split('=', 1)[0]
        if key in replacements:
            line = f'{key}={replacements[key]}'
            seen.add(key)
    lines.append(line)
for key, value in replacements.items():
    if key not in seen:
        lines.append(f'{key}={value}')
env.write_text('\n'.join(lines) + '\n')

def replace_kv(path, values):
    p = Path(path)
    out = []
    for line in p.read_text().splitlines():
        if '=' in line:
            key = line.split('=', 1)[0]
            if key in values:
                line = f'{key}={values[key]}'
        out.append(line)
    p.write_text('\n'.join(out) + '\n')

replace_kv('/etc/hostapd/hostapd.conf', {
    'interface': wifi,
    'ssid': ssid,
    'wpa_passphrase': wifi_pw,
})

Path('/etc/dnsmasq.d/pisowifi.conf').write_text(
    Path('/etc/dnsmasq.d/pisowifi.conf').read_text().replace(
        'interface=wlan0', f'interface={wifi}')
)

nft = Path('/etc/nftables.conf')
t = nft.read_text()
t = t.replace('iifname "wlan0"', f'iifname "{wifi}"')
t = t.replace('oifname "wlan0"', f'oifname "{wifi}"')
t = t.replace('iifname "eth0"', f'iifname "{wan}"')
t = t.replace('oifname "eth0"', f'oifname "{wan}"')
nft.write_text(t)
PY

# Debian's hostapd service reads DAEMON_CONF from this file on releases that use it.
if [[ -f /etc/default/hostapd ]]; then
  if grep -q '^DAEMON_CONF=' /etc/default/hostapd; then
    sed -i 's#^DAEMON_CONF=.*#DAEMON_CONF="/etc/hostapd/hostapd.conf"#' /etc/default/hostapd
  else
    printf '\nDAEMON_CONF="/etc/hostapd/hostapd.conf"\n' >> /etc/default/hostapd
  fi
fi

cat >/etc/sysctl.d/99-pisowifi.conf <<'SYSCTL'
net.ipv4.ip_forward=1
SYSCTL

mkdir -p /etc/NetworkManager/conf.d
cat >/etc/NetworkManager/conf.d/10-pisowifi-wlan.conf <<EOF2
[keyfile]
unmanaged-devices=interface-name:$WIFI_INTERFACE
EOF2

systemctl unmask hostapd.service || true
systemctl enable \
  pisowifi-network.service \
  hostapd.service \
  dnsmasq.service \
  nftables.service \
  pisowifi.service \
  pisowifi-coin.service \
  pisowifi-expire.timer || true

rm -f /var/lib/pisowifi/pisowifi.db

echo "PisoWiFi image customization complete."
