# Hardware wiring notes

Recommended signal chain:

Coin acceptor pulse output
→ level shifter / optocoupler if required
→ Orange Pi GPIO input
→ common ground only when electrically appropriate.

Verify:
1. GPIO voltage compatibility.
2. Active-high vs active-low pulse.
3. Pulse width.
4. Pulse count per denomination.
5. Whether the acceptor has an open-collector/open-drain output.

Do not assume a physical pin number is the same as a Linux GPIO line number. Use your OS's GPIO documentation and:

```bash
gpioinfo
```

to identify the correct chip and line.

For a ₱5 coin acceptor that produces 5 pulses:
`COIN_PULSES_PER_PESO=1`

For an acceptor that produces 1 pulse for ₱5, the pulse-to-denomination logic needs to be extended with a denomination map.
