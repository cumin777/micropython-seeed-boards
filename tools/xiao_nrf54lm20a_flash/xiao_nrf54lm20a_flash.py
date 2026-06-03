#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified pyOCD flashing script for Seeed XIAO nRF54LM20A.
"""

import argparse
import logging
import os
import subprocess
import sys
import tempfile
from importlib import import_module
from typing import Dict, List, Optional


def ensure_latest(packages: List[str]) -> None:
    if os.environ.get("SKIP_PYOCD_UPGRADE") == "1":
        print("[INFO] SKIP_PYOCD_UPGRADE=1 set; skipping auto-upgrade of dependencies.")
        return
    for pkg in packages:
        try:
            import_module(pkg)
        except Exception:
            pass
        print(f"[INFO] Ensuring latest {pkg} (pip install -U {pkg}) ...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-U", pkg], check=True)
        except subprocess.CalledProcessError as exc:
            print(f"[WARN] Failed to upgrade {pkg}: {exc}. Continuing if import works.")
            try:
                import_module(pkg)
            except Exception:
                print(f"[ERROR] {pkg} not installed and upgrade failed; aborting.")
                sys.exit(1)


ensure_latest(["intelhex", "pyocd"])

from intelhex import IntelHex
from pyocd.core.helpers import ConnectHelper
from pyocd.core.session import Session
from pyocd.flash.file_programmer import FileProgrammer
from pyocd.probe.aggregator import DebugProbeAggregator


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("nrf54lm20a_flasher")

NRF54LM20A_CORE_DEFINITIONS = {
    "Application": {
        "romBaseAddr": 0x00000000,
        "romSize": 0x001FD000,
        "uicrBaseAddr": 0x00FF8000,
        "uicrSize": 0x1000,
    },
}
NRF54LM20A_APPROTECT_ADDRESS = 0x00FF8208

PROTECTION_STATUS_NONE = "UNPROTECTED"
PROTECTION_STATUS_PROTECTED = "PROTECTED"
PROTECTION_STATUS_UNKNOWN = "UNKNOWN"


def read_word_safely(session: Session, addr: int) -> Optional[int]:
    try:
        return session.target.read32(addr)
    except Exception as exc:
        logger.debug("Read32 failed at 0x%08X: %s", addr, exc)
        return None


def detect_protection_status(session: Session) -> str:
    val = read_word_safely(session, NRF54LM20A_APPROTECT_ADDRESS)
    if val is not None:
        return PROTECTION_STATUS_NONE if (val & 0xFF) == 0xFF else PROTECTION_STATUS_PROTECTED
    return PROTECTION_STATUS_UNKNOWN


def get_core_info(session: Session) -> Dict[str, dict]:
    core_info = {}
    for core_name, core_def in NRF54LM20A_CORE_DEFINITIONS.items():
        if read_word_safely(session, core_def["romBaseAddr"]) is not None:
            core_info[core_name] = {**core_def, "accessible": True}
            logger.info("%s core detected and accessible.", core_name)
        else:
            core_info[core_name] = {**core_def, "accessible": False}
            logger.warning("%s core not accessible.", core_name)
    return core_info


def split_hex_by_core(hex_file: str, core_info: Dict[str, dict]) -> Dict[str, IntelHex]:
    merged_hex = IntelHex(hex_file)
    core_hexes = {}

    for core_name, core_def in core_info.items():
        if not core_def.get("accessible", False):
            continue

        core_hex = IntelHex()
        rom_start = core_def["romBaseAddr"]
        rom_end = rom_start + core_def["romSize"]
        uicr_start = core_def["uicrBaseAddr"]
        uicr_end = uicr_start + core_def["uicrSize"]

        for start, end in merged_hex.segments():
            for addr in range(start, end):
                if (rom_start <= addr < rom_end) or (uicr_start <= addr < uicr_end):
                    core_hex[addr] = merged_hex[addr]

        if len(core_hex) > 0:
            core_hexes[core_name] = core_hex
            logger.info("Data for %s core extracted from HEX file.", core_name)

    return core_hexes


def write_intelhex_to_temp(ih: IntelHex) -> str:
    fd, tmp_path = tempfile.mkstemp(suffix=".hex", prefix="nrf54lm20a_")
    os.close(fd)
    ih.write_hex_file(tmp_path)
    return tmp_path


def unlock_and_erase_device(session: Session) -> None:
    logger.info("Performing mass erase to unlock and erase the device...")
    target = session.target
    if detect_protection_status(session) == PROTECTION_STATUS_PROTECTED:
        logger.info("Protected device detected; mass erase is required to unlock.")
    target.mass_erase()
    logger.info("Mass erase completed successfully.")
    target.reset_and_halt()
    logger.info("Target halted after mass erase.")


def program_device(session: Session, core_hexes: Dict[str, IntelHex]) -> None:
    temp_files = []
    try:
        for core_name, core_hex in core_hexes.items():
            logger.info("Programming %s core...", core_name)
            temp_file = write_intelhex_to_temp(core_hex)
            temp_files.append(temp_file)
            programmer = FileProgrammer(
                session,
                progress=lambda p: logger.info("Programming progress: %.1f%%", p * 100),
            )
            programmer.program(temp_file, smart_flash=True)
            logger.info("%s core programming completed.", core_name)
    finally:
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)


def auto_select_hex() -> str:
    cwd = os.getcwd()
    merged_path = os.path.join(cwd, "merged.hex")
    if os.path.isfile(merged_path):
        logger.info("Auto-selected HEX: %s (found merged.hex)", merged_path)
        return merged_path

    hex_files = [f for f in os.listdir(cwd) if f.lower().endswith(".hex")]
    if not hex_files:
        logger.error("No HEX file found in current directory.")
        sys.exit(1)
    if len(hex_files) == 1:
        candidate = os.path.join(cwd, hex_files[0])
        logger.info("Auto-selected HEX: %s (only hex file)", candidate)
        return candidate

    hex_files_full = [os.path.join(cwd, f) for f in hex_files]
    hex_files_full.sort(key=lambda path: os.path.getmtime(path), reverse=True)
    candidate = hex_files_full[0]
    logger.info("Auto-selected HEX: %s (most recently modified)", candidate)
    return candidate


def main() -> None:
    parser = argparse.ArgumentParser(description="Unlock and flash Seeed XIAO nRF54LM20A firmware.")
    parser.add_argument("--hex", help="Path to the HEX file to be programmed.")
    parser.add_argument("--probe", help="Specify the unique ID of the debug probe to use.")
    args = parser.parse_args()

    if args.probe:
        probe_id = args.probe
        logger.info("Using specified probe: %s", probe_id)
    else:
        probes = DebugProbeAggregator.get_all_connected_probes()
        if not probes:
            logger.error("No connected debug probes found.")
            sys.exit(1)
        if len(probes) > 1:
            logger.error("Multiple probes connected. Please specify one with --probe <unique_id>:")
            for probe in probes:
                logger.error("  - %s : %s", probe.unique_id, probe.description)
            sys.exit(1)
        probe_id = probes[0].unique_id
        logger.info("Auto-selected probe: %s (%s)", probe_id, probes[0].description)

    if not args.hex:
        args.hex = auto_select_hex()

    logger.info("Using HEX file: %s", args.hex)
    session_options = {
        "target_override": "nrf54l",
        "connect_mode": "under-reset",
    }

    try:
        with ConnectHelper.session_with_chosen_probe(unique_id=probe_id, **session_options) as session:
            logger.info("Successfully connected to target.")
            unlock_and_erase_device(session)
            core_info = get_core_info(session)
            if not any(info.get("accessible") for info in core_info.values()):
                logger.error("No accessible cores found.")
                sys.exit(1)
            core_hexes = split_hex_by_core(args.hex, core_info)
            if not core_hexes:
                logger.error("No relevant data found in the HEX file for the accessible cores.")
                sys.exit(1)
            program_device(session, core_hexes)
            logger.info("Resetting target to run application...")
            session.target.reset()
            logger.info("nRF54LM20A programming completed successfully.")
    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user.")
    except Exception as exc:
        logger.error("An error occurred: %s", exc, exc_info=True)
        sys.exit(2)


if __name__ == "__main__":
    main()
