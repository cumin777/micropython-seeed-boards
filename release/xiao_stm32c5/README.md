# XIAO STM32C5 MicroPython — Delivery Package

This package lets an Application Engineer (AE) **flash** a prebuilt MicroPython
firmware onto the Seeed **XIAO STM32C5**, **open the REPL**, and **run the
on-board hardware test** — no toolchain, no build step, no ST-Link/J-Link
required.

> Board: STM32C5A3CG (Cortex-M33). Firmware: MicroPython on Zephyr, flashed as
> a UF2 through the on-board TinyUF2 bootloader.

## 1. Package contents

| Path | What it is |
|---|---|
| `firmware/micropython-xiao-stm32c5.uf2` | The firmware image — copy this to the board. |
| `firmware/SHA256SUMS.txt` | SHA-256 checksums for the firmware and the test script. |
| `tests/xiao_stm32c5_full_test.py` | Hardware test script — upload to the board and run. |
| `flash_xiao_stm32c5.sh` | Optional helper to copy the UF2 on Linux/macOS. |
| `README.md` | This document. |
| `RELEASE_NOTES.md` | Build/version evidence and known limitations. |
| `LICENSE` | Firmware license. |

## 2. Prerequisites

- One **XIAO STM32C5** board.
- A **USB-C cable** (data + power) for flashing.
- A **3.3 V USB-TTL serial adapter** for the REPL (the v1 REPL is on **USART1**,
  not USB). Pins: **PA9 = TX**, **PA10 = RX**, **GND** → board GND.
- A serial terminal: `picocom`, `screen`, `putty`, or the Thonny serial monitor.
  Settings: **115200 baud, 8-N-1, no flow control**.
- A way to copy the test script onto the board filesystem (Thonny / `mpremote`,
  or paste into REPL).

No Python, PlatformIO, Zephyr SDK, ST-Link, or J-Link is needed for flashing.

## 3. Flash the firmware

1. Connect the board over USB.
2. **Double-click the Reset button** quickly. The board enters the TinyUF2
   bootloader and exposes a mass-storage drive named **`XIAOC5BOOT`**.
3. Copy `firmware/micropython-xiao-stm32c5.uf2` onto that drive:
   - **Drag-and-drop** the file onto `XIAOC5BOOT` (any OS), or
   - **Linux/macOS helper**: with the board in bootloader mode, run
     `./flash_xiao_stm32c5.sh` (it locates `XIAOC5BOOT` and copies the file).
4. The board **reboots automatically** when the copy completes. `XIAOC5BOOT`
   disappears and MicroPython starts.

**Verify the checksum** before distributing (recommended):

```bash
cd firmware
sha256sum -c SHA256SUMS.txt        # Linux / macOS (Git Bash)
# Windows PowerShell: compare Get-FileHash output to SHA256SUMS.txt
```

### Flash troubleshooting / recovery

- **`XIAOC5BOOT` doesn't appear:** unplug/replug USB and double-click Reset
  again. Use a data-capable USB cable (charge-only cables won't work).
- **You flashed a wrong/broken UF2:** the TinyUF2 bootloader is **not**
  overwritten by an application UF2. Double-click Reset to re-enter the
  bootloader and copy a known-good image — the board is always recoverable.
- **Wrong-family UF2:** only a UF2 built for STM32C5 (family `0x00C5C5C5`)
  applies; TinyUF2 rejects mismatched families.

## 4. Open the REPL (USART1)

The v1 MicroPython REPL runs on **USART1** (`PA9` TX / `PA10` RX), 115200 8-N-1.

1. Wire the serial adapter: adapter **RX → PA9**, adapter **TX → PA10**,
   adapter **GND → board GND**. (Board TX goes to adapter RX.)
2. Open a terminal, for example:

   ```bash
   picocom -b 115200 /dev/ttyUSB0          # Linux
   # screen /dev/tty.usbserial-* 115200    # macOS
   ```
3. Press **Ctrl-C** or tap **Reset** once — you should see the MicroPython
   banner and the `>>>` REPL prompt.

> USB-CDC REPL and 1200-bps auto-bootloader-entry are **not** part of this v1
> build; use the USART1 REPL and the double-reset bootloader entry.

## 5. Run the hardware test

The single entry point runs every peripheral test and prints a per-item result.

1. Copy `tests/xiao_stm32c5_full_test.py` onto the board filesystem (Thonny →
   save to device, or `mpremote cp tests/xiao_stm32c5_full_test.py :/`).
2. At the REPL:

   ```python
   import xiao_stm32c5_full_test as test
   test.main()
   ```

### Reading the results

Each item prints one of:

| Tag | Meaning |
|---|---|
| `[PASS]` | The peripheral works. |
| `[SKIP]` | Skipped — the external hardware it needs is absent (e.g. no CAN bus, no battery). **Expected on a bare board; not a failure.** |
| `[FAIL]` | The peripheral did not behave as expected — investigate. |

The run ends with a summary line, e.g. `PASS=18 FAIL=0 SKIP=4`.

**Coverage:** LED, GPIO (D0–D15), ADC, PWM, I2C1, on-board LSM6DS3TR-C IMU,
battery sense, UART loopback, RTC, LittleFS storage, and the FDCAN2 (CAN-FD)
regression suite (9 cases, self-loopback). Every wait is bounded, so a missing
transceiver or bus **cannot hang** the test.

### Typical outcomes on a bare board

- **CAN cases** mostly `PASS` — the test uses FDCAN internal loopback, so no
  external bus is required. External two-board CAN testing needs CANH↔CANH,
  CANL↔CANL with 120 Ω termination.
- **Battery = SKIP** when no battery is attached; with `BAT_EN` (PE2) and the
  sense divider on PA4 it reports a voltage when present.
- **IMU** tests the on-board LSM6DS3TR-C on I2C2 (`0x6A`); no external wiring.

## 6. Peripheral / wiring reference (XIAO header)

| Function | Pin | Notes |
|---|---|---|
| USART1 REPL | PA9 (TX), PA10 (RX) | 115200 8-N-1; don't run UART-loopback test while using it as REPL. |
| User LED | PB12 | Driven by the LED test. |
| I2C1 (header) | D4=PB7 (SDA), D5=PB6 (SCL) | External I2C devices. |
| IMU (on-board) | I2C2 PB3 (SDA) / PB4 (SCL) | LSM6DS3TR-C @ `0x6A`. |
| PWM | PA8 / TIM1_CH1 | Verify with scope / LED / test point. |
| ADC | PA0–PA4 (ADC1_IN0–IN4) | PA4 = battery sense. |
| Battery enable | PE2 (`BAT_EN`) | Enable the sense divider before reading. |
| FDCAN2 | PB5 (RX), PB13 (TX), PB14 (STB) | Needs a CAN transceiver + 120 Ω bus for external testing. |

## 7. Status

This is a **functionally-built** package — MicroPython on Zephyr, validated to
compile and link against official MicroPython **`v1.27.0`** and Zephyr
**`4.4.0`**. It is **not** a formal hardware-qualified release until a real XIAO
STM32C5 has passed: TinyUF2 upgrade **and** rollback, wrong-UF2 recovery, ten
update/boot cycles, and the complete function test. Record those results in
`RELEASE_NOTES.md` before publishing a tagged release.

For build-from-source instructions and the Zephyr/patch mechanism, see the
top-level repository `README.md`.
