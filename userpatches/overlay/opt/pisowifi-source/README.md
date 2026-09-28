# PisoWiFi Orange Pi Zero 3 — Version 2

Editable PisoWiFi platform for Orange Pi Zero 3.

## V2 features

- ₱5 / ₱10 / ₱20 / ₱50 fixed plans
- GPIO coin-slot pulse input
- Automatic voucher generation after payment
- Live customer session timer
- Per-plan speed limits
- Per-plan data limits
- Mobile-first customer UI
- Admin dashboard
- SQLite
- nftables
- systemd
- Configurable GPIO and coin pulse mapping

## Default plans

| Price | Time | Speed | Data |
|---:|---:|---:|---:|
| ₱5 | 30 min | 2 Mbps | 300 MB |
| ₱10 | 60 min | 4 Mbps | 700 MB |
| ₱20 | 180 min | 6 Mbps | 2 GB |
| ₱50 | 1440 min | 10 Mbps | 8 GB |

Edit `config/plans.json`.

## Coin slot

The coin acceptor should provide a clean logic pulse to a suitable GPIO input. **Do not connect a coin acceptor output directly to a GPIO until its voltage level is verified.** Use a level shifter/isolator when necessary.

Configure:

`COIN_GPIO_CHIP` and `COIN_GPIO_LINE`

The example uses `gpiod`/libgpiod rather than assuming a physical header number.

A pulse-counting adapter can be configured with:

`COIN_PULSES_PER_PESO`

Example: if the coin acceptor outputs 1 pulse per ₱1, use 1. If it outputs 5 pulses for a ₱5 coin, use 5.

## Important

The coin daemon creates credit from pulses; it does not know whether the pulse really came from a coin acceptor. Use electrical filtering/debouncing and a properly isolated input.

The speed/data enforcement is implemented with Linux traffic control and nftables. The exact kernel capabilities can vary between Orange Pi images.

This remains a source project rather than a universal SD-card image. Install it on a compatible Debian/Armbian Orange Pi Zero 3 image.

## Install

```bash
sudo bash install.sh
```

Then reboot.

Portal:

`http://10.10.0.1:8080`

Admin:

`http://10.10.0.1:8080/admin`

## Test coin input

Before connecting the coin acceptor, run:

```bash
sudo systemctl stop pisowifi-coin
sudo /opt/pisowifi/venv/bin/python /opt/pisowifi/coin/coin_daemon.py --test
```

This only reports pulses and does not create credit.

## Safety

GPIO voltage levels are hardware-specific. Verify the Orange Pi Zero 3 GPIO electrical limits and the coin acceptor output before wiring.
