#!/bin/bash
set -euo pipefail
[ "$EUID" -eq 0 ] || { echo "Run with sudo"; exit 1; }
P="$(cd "$(dirname "$0")" && pwd)"
mkdir -p /opt/pisowifi /etc/pisowifi /var/lib/pisowifi
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv python3-pip hostapd dnsmasq nftables iproute2 iw iproute2 gpiod python3-libgpiod
cp -a "$P/portal" "$P/coin" "$P/scripts" /opt/pisowifi/
cp "$P/config/plans.json" /etc/pisowifi/plans.json
cp "$P/config/pisowifi.env.example" /etc/pisowifi/pisowifi.env
cp "$P/config/hostapd.conf" /etc/hostapd/hostapd.conf
cp "$P/config/dnsmasq.conf" /etc/dnsmasq.d/pisowifi.conf
cp "$P/config/nftables.conf" /etc/nftables.conf

read -rp "Wi-Fi interface [wlan0]: " W; W=${W:-wlan0}
read -rp "WAN interface [eth0]: " E; E=${E:-eth0}
read -rp "SSID [PisoWiFi]: " S; S=${S:-PisoWiFi}
read -rsp "Wi-Fi password: " WP; echo
read -rsp "Admin password: " AP; echo
read -rp "GPIO chip [/dev/gpiochip0]: " GC; GC=${GC:-/dev/gpiochip0}
read -rp "GPIO line [6]: " GL; GL=${GL:-6}
sed -i -e "s/^WIFI_INTERFACE=.*/WIFI_INTERFACE=$W/" -e "s/^WAN_INTERFACE=.*/WAN_INTERFACE=$E/" \
 -e "s/^WIFI_SSID=.*/WIFI_SSID=$S/" -e "s/^WIFI_PASSWORD=.*/WIFI_PASSWORD=$WP/" \
 -e "s/^ADMIN_PASSWORD=.*/ADMIN_PASSWORD=$AP/" -e "s#^COIN_GPIO_CHIP=.*#COIN_GPIO_CHIP=$GC#" \
 -e "s/^COIN_GPIO_LINE=.*/COIN_GPIO_LINE=$GL/" /etc/pisowifi/pisowifi.env
sed -i "s/interface=wlan0/interface=$W/;s/ssid=PisoWiFi/ssid=$S/;s/wpa_passphrase=.*/wpa_passphrase=$WP/" /etc/hostapd/hostapd.conf
sed -i "s/interface=wlan0/interface=$W/" /etc/dnsmasq.d/pisowifi.conf
sed -i "s/\"wlan0\"/\"$W\"/g;s/\"eth0\"/\"$E\"/g" /etc/nftables.conf

python3 -m venv /opt/pisowifi/venv
/opt/pisowifi/venv/bin/pip install --upgrade pip
/opt/pisowifi/venv/bin/pip install Flask==3.1.0 Werkzeug==3.1.3

install -m 0644 "$P/systemd/"*.service "$P/systemd/"*.timer /etc/systemd/system/
install -m 0755 "$P/scripts/tc_setup.py" /usr/local/sbin/pisowifi-tc
install -m 0755 "$P/scripts/expire_sessions.py" /opt/pisowifi/scripts/expire_sessions.py

cat >/etc/sysctl.d/99-pisowifi.conf <<EOF
net.ipv4.ip_forward=1
EOF
sysctl --system >/dev/null
systemctl unmask hostapd || true
systemctl enable hostapd dnsmasq nftables pisowifi pisowifi-coin pisowifi-expire.timer
nft -f /etc/nftables.conf || true
/usr/local/sbin/pisowifi-tc init || true
systemctl restart nftables || true
systemctl restart dnsmasq || true
systemctl restart hostapd || true
systemctl restart pisowifi
systemctl restart pisowifi-coin || true
echo "Installed V2. Reboot recommended."
