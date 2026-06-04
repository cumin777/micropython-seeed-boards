#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flashing helper for Seeed XIAO nRF54LM20A.

This script intentionally mirrors the working platform-seeedboards strategy:
- ensure a pyOCD build that exposes the nrf54lm20a target
- invoke `python -m pyocd flash ...` directly
- avoid custom low-level FileProgrammer logic
"""

import argparse
import os
import subprocess
import sys

PYOCD_SPEC = "pyocd @ git+https://github.com/StarSphere-1024/pyOCD.git@lm20_stable"
TARGET = "nrf54lm20a"
FREQUENCY = "4000000"


def ensure_expected_pyocd() -> None:
    if os.environ.get("SKIP_PYOCD_UPGRADE") == "1":
        print("[INFO] SKIP_PYOCD_UPGRADE=1 set; skipping pyOCD compatibility check.")
        return

    try:
        output = subprocess.check_output(
            [sys.executable, "-m", "pyocd", "list", "--targets"],
            stderr=subprocess.STDOUT,
            text=True,
        )
        if TARGET in output.lower():
            print(f"[INFO] Detected pyOCD target support for {TARGET}.")
            return
    except Exception:
        pass

    print(f"[INFO] Installing pyOCD fork with {TARGET} support ...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", PYOCD_SPEC, "libusb"], check=True)


def auto_select_probe() -> str:
    output = subprocess.check_output(
        [sys.executable, "-m", "pyocd", "list", "--probes", "--no-header"],
        stderr=subprocess.STDOUT,
        text=True,
    )

    probes = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if parts:
            probes.append(parts[0])

    if not probes:
        print("[ERROR] No connected debug probes found.")
        sys.exit(1)
    if len(probes) > 1:
        print("[ERROR] Multiple probes connected. Please specify one with --probe <unique_id>:")
        for probe in probes:
            print(f"  - {probe}")
        sys.exit(1)

    print(f"[INFO] Auto-selected probe: {probes[0]}")
    return probes[0]


def auto_select_hex() -> str:
    cwd = os.getcwd()
    merged_path = os.path.join(cwd, "merged.hex")
    if os.path.isfile(merged_path):
        print(f"[INFO] Auto-selected HEX: {merged_path} (found merged.hex)")
        return merged_path

    hex_files = [f for f in os.listdir(cwd) if f.lower().endswith(".hex")]
    if not hex_files:
        print("[ERROR] No HEX file found in current directory.")
        sys.exit(1)
    if len(hex_files) == 1:
        candidate = os.path.join(cwd, hex_files[0])
        print(f"[INFO] Auto-selected HEX: {candidate} (only hex file)")
        return candidate

    hex_files_full = [os.path.join(cwd, f) for f in hex_files]
    hex_files_full.sort(key=lambda path: os.path.getmtime(path), reverse=True)
    candidate = hex_files_full[0]
    print(f"[INFO] Auto-selected HEX: {candidate} (most recently modified)")
    return candidate


def main() -> None:
    parser = argparse.ArgumentParser(description="Flash Seeed XIAO nRF54LM20A firmware with pyOCD.")
    parser.add_argument("--hex", help="Path to the HEX file to be programmed.")
    parser.add_argument("--probe", help="Specify the unique ID of the debug probe to use.")
    args = parser.parse_args()

    ensure_expected_pyocd()

    probe_id = args.probe or auto_select_probe()
    hex_path = args.hex or auto_select_hex()

    print(f"[INFO] Using HEX file: {hex_path}")
    cmd = [
        sys.executable,
        "-m",
        "pyocd",
        "flash",
        "--probe",
        probe_id,
        "--target",
        TARGET,
        "--frequency",
        FREQUENCY,
        hex_path,
    ]

    print("[INFO] Running:", " ".join(cmd))
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
