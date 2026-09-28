#!/usr/bin/env python3
import os
import time
import signal
import argparse
import json
import select
from datetime import datetime, timedelta

import sys
sys.path.insert(0, "/opt/pisowifi/portal")
import db


def settings():
    return {
        "chip": os.getenv("COIN_GPIO_CHIP", "/dev/gpiochip0"),
        "line": int(os.getenv("COIN_GPIO_LINE", "6")),
        "active_high": os.getenv("COIN_ACTIVE_HIGH", "1") == "1",
        "min_ms": int(os.getenv("COIN_PULSE_MIN_MS", "30")),
        "max_ms": int(os.getenv("COIN_PULSE_MAX_MS", "1000")),
        "debounce": int(os.getenv("COIN_DEBOUNCE_MS", "80")),
        "peso_pulses": int(os.getenv("COIN_PULSES_PER_PESO", "1")),
    }


def create_voucher_for_pesos(pesos):
    with open("/etc/pisowifi/plans.json") as f:
        plans = json.load(f)
    p = str(int(pesos))
    if p not in plans:
        return None
    x = plans[p]
    return db.create_voucher(
        int(p), x["name"], x["minutes"], x["speed_mbps"], x["data_mb"]
    )


def record_peso():
    code = create_voucher_for_pesos(1)
    db.add_coin_event(settings()["peso_pulses"], 1)
    if code:
        print(f"VOUCHER 1 {code}", flush=True)


def run_gpio(test_only=False):
    try:
        import gpiod
        from gpiod.line import Bias, Direction, Edge
    except ImportError:
        raise RuntimeError("python3-libgpiod is not installed")

    s = settings()
    # The active level determines which edge represents a pulse.
    edge = Edge.BOTH
    debounce = timedelta(milliseconds=max(0, s["debounce"]))

    with gpiod.request_lines(
        s["chip"],
        consumer="pisowifi-coin",
        config={
            s["line"]: gpiod.LineSettings(
                direction=Direction.INPUT,
                edge_detection=edge,
                bias=Bias.PULL_UP,
                active_low=not s["active_high"],
                debounce_period=debounce,
            )
        },
    ) as request:
        print(f"GPIO monitor: {s}", flush=True)
        last_active_ns = None
        pulse_count = 0

        while True:
            for event in request.read_edge_events():
                rising = event.event_type is event.Type.RISING_EDGE
                falling = event.event_type is event.Type.FALLING_EDGE
                active_edge = rising if s["active_high"] else falling
                now_ns = event.timestamp_ns

                if not active_edge:
                    continue

                if last_active_ns is not None:
                    gap_ms = (now_ns - last_active_ns) / 1_000_000
                    if gap_ms < s["debounce"]:
                        continue
                last_active_ns = now_ns

                if test_only:
                    print(
                        f"pulse edge at {datetime.now().isoformat(timespec='seconds')}",
                        flush=True,
                    )
                    continue

                pulse_count += 1
                if pulse_count >= s["peso_pulses"]:
                    pesos = pulse_count // s["peso_pulses"]
                    pulse_count %= s["peso_pulses"]
                    # Current plans are fixed denominations. A pulse stream is
                    # converted to a denomination only when that denomination exists.
                    with open("/etc/pisowifi/plans.json") as f:
                        plans = json.load(f)
                    denomination = str(pesos)
                    if denomination in plans:
                        x = plans[denomination]
                        db.add_coin_event(pesos * s["peso_pulses"], pesos)
                        code = db.create_voucher(
                            pesos, x["name"], x["minutes"],
                            x["speed_mbps"], x["data_mb"]
                        )
                        print(f"VOUCHER {pesos} {code}", flush=True)
                    else:
                        print(f"UNMAPPED_PULSES {pesos}", flush=True)


def test_source():
    source = os.getenv("COIN_PULSE_SOURCE", "")
    if not source:
        print("No COIN_PULSE_SOURCE configured.", flush=True)
        return
    import subprocess
    p = subprocess.Popen(source, shell=True, stdout=subprocess.PIPE, text=True)
    for line in p.stdout:
        try:
            n = int(line.strip())
        except ValueError:
            continue
        print(f"SOURCE_PULSE {n}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args()
    db.init_db()

    source = os.getenv("COIN_PULSE_SOURCE", "")
    if source:
        return test_source() if args.test else test_source()

    run_gpio(test_only=args.test)


if __name__ == "__main__":
    main()
