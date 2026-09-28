# Coin slot integration

The V2 architecture separates the coin hardware from the web application.

A coin event becomes a peso amount, then the daemon looks up that exact plan and generates a voucher.

Examples:

- 5 pulses → ₱5 voucher
- 10 pulses → ₱10 voucher
- 20 pulses → ₱20 voucher
- 50 pulses → ₱50 voucher

Set `COIN_PULSES_PER_PESO` to match your acceptor.

For hardware-specific GPIO event reading, use libgpiod. The exact Python GPIO API differs across Debian/Armbian releases, so `COIN_PULSE_SOURCE` is supported as a portable integration point: it should output one integer per detected pulse.

Never connect an unknown-voltage signal directly to an Orange Pi GPIO.
