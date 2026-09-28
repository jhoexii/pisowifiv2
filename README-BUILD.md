# PisoWiFi Orange Pi Zero 3 — flashable image build kit

This kit turns the supplied PisoWiFi V2 source project into a bootable Armbian
Debian 13 (Trixie) image for **Orange Pi Zero 3**.

## What it does

- Builds the Orange Pi Zero 3 bootloader/kernel/root filesystem using Armbian.
- Installs the PisoWiFi portal, SQLite database, hostapd, dnsmasq, nftables and GPIO support.
- Fixes the missing `json` import in the Flask app.
- Uses the libgpiod v2 Python API used by current Debian Trixie.
- Gives `wlan0` the 10.10.0.1/24 hotspot address.
- Adds IPv4 masquerading so authorized Wi-Fi clients can reach the WAN.
- Makes the hotspot services start in the correct order.
- Leaves Armbian's normal first-boot user setup enabled.

## Build machine

Use a Linux x86-64 machine (Ubuntu 24.04 is a practical choice) with at least
8 GB RAM and roughly 50 GB free disk. Armbian documents these as its current
build requirements.

Install Git and sudo/build prerequisites as needed, then:

```bash
cp build.env.example build.env
nano build.env
chmod +x build-image.sh
./build-image.sh
```

The finished `.img.xz` will be under:

```text
armbian-build/output/images/
```

## Flash

On Linux:

```bash
xz -dk Armbian-*.img.xz
sudo dd if=Armbian-*.img of=/dev/sdX bs=4M status=progress conv=fsync
sync
```

Replace `/dev/sdX` with the **whole SD card**, not a partition.

On Windows, use a raw-image flasher such as Raspberry Pi Imager, Balena
Etcher, or another SD-card imaging tool and select the generated `.img.xz`.

## First boot

Connect:

- Orange Pi Zero 3 Ethernet -> upstream/router
- Wi-Fi clients -> the configured PisoWiFi SSID
- Coin acceptor -> the configured GPIO through the required electrical
  isolation/level shifting

The portal is:

```text
http://10.10.0.1:8080
http://10.10.0.1:8080/admin
```

The build defaults to:

```text
WAN: eth0
AP:  wlan0
AP IP: 10.10.0.1
GPIO: /dev/gpiochip0 line 6
```

**Verify the actual GPIO line on your OS with `gpioinfo`. Do not assume a
physical header pin number equals the Linux GPIO line number.**

## Important project limitation

The current source advertises per-plan data limits, but the supplied code does
not yet implement byte-accurate data accounting/enforcement. Speed shaping is
also a simple outbound `tc` implementation. The image build makes the system
bootable; those accounting features should be treated as the next development
step rather than assuming they are already production-grade.

## Security

Change both passwords in `build.env` before building. Do not publish a built
image containing your real admin/Wi-Fi credentials.

The coin acceptor output must be electrically compatible with the Orange Pi
GPIO. Use a level shifter or optocoupler when required.
