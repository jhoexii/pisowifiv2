# GitHub build — PisoWiFi Orange Pi Zero 3

This repository is prepared for a one-click GitHub Actions build of a custom
Armbian image for the Orange Pi Zero 3.

## Upload to GitHub

Upload **all files in this repository**, preserving the `.github/workflows/`
and `userpatches/` directories. Do not upload your local `/root/armbian-build`
directory.

## Build

1. Open the repository on GitHub.
2. Open **Actions**.
3. Select **Build PisoWiFi Orange Pi Zero 3**.
4. Click **Run workflow**.
5. Enter the Wi-Fi SSID/password and admin password.
6. Verify the GPIO line for your coin acceptor before using it.
7. Start the workflow.
8. When it completes, open the workflow run and download the artifact named
   `pisowifi-orangepi-zero3-image`.

The workflow uses Armbian's official build framework/action and current Debian
Trixie userspace. Armbian documents `userpatches/customize-image.sh` and the
`userpatches/overlay/` mechanism for installing files into a generated image.

## Flashing

The artifact contains an `.img.xz`. Flash it to the **whole** microSD card,
not an individual partition. Raspberry Pi Imager, balenaEtcher, or a Linux
`dd` workflow can write it.

## Hardware defaults

- Board: Orange Pi Zero 3
- WAN: `eth0`
- AP: `wlan0`
- AP IP: `10.10.0.1`
- Portal: `http://10.10.0.1:8080`
- Admin: `http://10.10.0.1:8080/admin`
- GPIO default: `/dev/gpiochip0` line `6`
- Timezone: `Asia/Manila`

**Important:** a physical header pin number is not necessarily the Linux GPIO
line number. Confirm the line with `gpioinfo` on the actual Orange Pi image.
Also verify that the coin acceptor's output voltage is electrically safe for
the Orange Pi GPIO; use isolation/level shifting where required.

## Important project limitation

The current source has database fields for data usage, but it does not yet
implement byte-accurate per-client data accounting/enforcement. The current
traffic shaping helper is also intentionally simple and primarily shapes
outbound traffic.
