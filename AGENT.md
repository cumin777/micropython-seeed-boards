# XIAO NRF54LM20A MicroPython Adaptation Agent Guide

## 1. Objective

This document is the execution contract for fully adapting `xiao_nrf54lm20a` into `D:\workspace\micropython_seeed_board\micropython-seeed-boards`, producing a user-deliverable firmware package, and continuing development until the port is complete.

Target outcome:

- `xiao_nrf54lm20a` is buildable from this repository against `lib/micropython` Zephyr port.
- The firmware boots to MicroPython REPL and supports the board-level APIs expected by this repository.
- A user-facing flash package equivalent to `C:\Users\seeed\Downloads\xiao54_flash` is produced for `xiao_nrf54lm20a`.

## 2. Mandatory Execution Rules

These rules are binding for all subsequent automated work.

1. Every effective modification must be committed to `https://github.com/cumin777/micropython-seeed-boards.git`.
2. All work must happen on branch `nrf54lm20a_support`.
3. The requested base branch `main` does not exist in the current remote. The repository currently exposes `origin/master` only, so `nrf54lm20a_support` has been created from `origin/master`. Treat this as the canonical base unless the remote branch model changes later.
4. After each effective modification, append a short entry to the progress log in this file before or together with the commit.
5. Follow the superpowers MCP workflow for the whole development:
   - Use planning before implementation for multi-step work.
   - Use systematic debugging before speculative fixes when builds or runtime validation fail.
   - Use code review workflow before final delivery / merge readiness.
6. Do not stop adaptation work until the full port, validation, packaging, and documentation are complete, unless blocked by a hard external dependency.
7. Do not revert unrelated user changes in the worktree.
8. Keep commits small and scoped to one effective step whenever practical.

## 3. Repository Reality Check

This repository is not a standalone full MicroPython tree. It is a Seeed integration repository with:

- board definitions under `boards/`
- custom helper C modules under `src/cmodules/`
- user examples under `example/`
- flash tooling under `tools/`
- upstream MicroPython pulled as submodule at `lib/micropython`

Important implication:

- Most `xiao_nrf54lm20a` enablement will be implemented by combining this repository's board/overlay/tooling changes with targeted changes inside `lib/micropython` when the Zephyr port or board detection requires it.

## 4. Current Reference Implementation

The closest in-repo reference is `xiao_nrf54l15`.

Relevant existing implementation points:

- Zephyr board definition:
  - `boards/seeed/xiao_nrf54l15/`
- Zephyr build overrides for MicroPython:
  - `boards/xiao_nrf54l15_nrf54l15_cpuapp.conf`
  - `boards/xiao_nrf54l15_nrf54l15_cpuapp.overlay`
  - `boards/pm_static_xiao_nrf54l15_nrf54l15_cpuapp.yml`
- Flash package tooling:
  - `tools/xiao_nrf54l15_flash/`
- Python-side board aliasing:
  - `example/boards/xiao.py`
  - `example/boards/xiao_nrf54l15.py`

The user-provided hardware source of truth for the new target is:

- `D:\workspace\platform-seeedboards\zephyr\boards\arm\xiao_nrf54lm20a`

This Zephyr board directory already contains:

- `board.cmake`
- `board.yml`
- `Kconfig.xiao_nrf54lm20a`
- CPUAPP / CPUFLPR DTS and YAML files
- common DTSI and pinctrl DTSI
- connector DTSI and docs/support directories

## 5. Technical Findings That Must Drive The Port

### 5.1 Current MicroPython integration model

`README.md` shows the nRF54L15 build is done by invoking `west build` on `lib/micropython/ports/zephyr` with:

- `--sysbuild`
- `-DBOARD_ROOT=<repo root>`
- `-DEXTRA_DTC_OVERLAY_FILE=<repo root>/boards/...overlay`
- `-DPM_STATIC_YML_FILE=<repo root>/boards/...pm_static...yml`
- `-DEXTRA_CONF_FILE=<repo root>/boards/...conf`

This means `xiao_nrf54lm20a` support needs both:

- a Zephyr board definition visible through `BOARD_ROOT`
- a MicroPython-specific overlay / config / partition scheme at repository root

### 5.2 Existing user modules required by Seeed examples

The repository uses custom modules from:

- `src/cmodules/modadc`
- `src/cmodules/modlowpwr`
- `src/cmodules/modpdm`
- `src/cmodules/modrtc`

`boards/seeed/xiao_nrf54l15/pre_dt_board.cmake` wires these through `USER_C_MODULES`.

Implication:

- `xiao_nrf54lm20a` must preserve or deliberately redefine this module set based on actual hardware support.
- If the board lacks feature parity for a module, that gap must be explicitly handled in examples and user guidance, not silently ignored.

### 5.3 Python board abstraction layer

`example/boards/xiao.py` dispatches by `implementation._machine` and imports `boards.xiao_nrf54l15`.

Implication:

- `xiao_nrf54lm20a` needs a new Python board map module.
- The dispatcher must detect the new machine string emitted by the built firmware.
- Pin / ADC / PWM / I2C / SPI / UART / PDM mappings must match the actual DTS-based hardware routing.

### 5.4 Packaging model

Reference package `C:\Users\seeed\Downloads\xiao54_flash` contains:

- `flash.bat`
- `merged.hex`
- `xiao_nrf54l15.hex`
- `xiao_nrf54l15_recover_flash.py`

Implication:

- Final deliverable for `xiao_nrf54lm20a` should follow the same user experience:
  - one archive directory
  - one-click flashing entrypoint
  - the final `.hex` artifacts
  - a Python recover/program script adapted for the new SoC / target naming

## 6. High-Level Porting Strategy

Implement in this order:

1. Board import and build plumbing
2. MicroPython Zephyr build enablement
3. Python board abstraction and examples
4. Flash tooling and packaged deliverable
5. Hardware validation and user-facing instructions

Reason:

- The board must build before Python abstraction can be verified.
- The flash package depends on stable build outputs and target memory layout.
- User examples only matter after firmware boots and exposes expected peripherals.

## 7. Planned File Structure Changes

Expected repository additions / modifications:

- Create `boards/seeed/xiao_nrf54lm20a/`
  - imported and normalized from `D:\workspace\platform-seeedboards\zephyr\boards\arm\xiao_nrf54lm20a`
- Create MicroPython build override files at repo root:
  - `boards/xiao_nrf54lm20a_nrf54lm20a_cpuapp.conf`
  - `boards/xiao_nrf54lm20a_nrf54lm20a_cpuapp.overlay`
  - `boards/pm_static_xiao_nrf54lm20a_nrf54lm20a_cpuapp.yml`
- Create flash tool directory:
  - `tools/xiao_nrf54lm20a_flash/`
- Create Python board alias file:
  - `example/boards/xiao_nrf54lm20a.py`
- Modify Python dispatcher:
  - `example/boards/xiao.py`
- Update top-level docs as needed:
  - `README.md`
- Possibly modify submodule content:
  - `lib/micropython/ports/zephyr/...`
  - only when the upstream Zephyr port needs board detection / config changes for this SoC

## 8. Detailed Execution Plan

### Phase A. Baseline import and diff against nRF54L15

Goals:

- copy the Zephyr board definition into this repo
- compare nRF54LM20A vs nRF54L15 pinmux, peripherals, board runners, and memory assumptions

Required checks:

- fix any naming inconsistencies from the source board files before adoption
- verify CPUAPP and CPUFLPR filenames, DTS includes, and compatible strings
- verify `board.cmake` target names for openocd / jlink / nrfutil

Known issue already found:

- `xiao_nrf54lm20a_nrf54lm20a_cpuflpr.dts` includes `"xiao_nrf54lm20_nrf54lm20a-common.dtsi"`, which appears to be a filename typo and must be confirmed/corrected during import.

### Phase B. Recreate MicroPython-specific board overlays

Goals:

- define the MicroPython runtime feature set for `cpuapp`
- create storage partition layout for filesystem
- wire up any optional peripherals required by Seeed examples

Starting point:

- derive from the three existing nRF54L15 files at repo root

Decision points to resolve explicitly:

- whether LittleFS partition size and application size should follow nRF54L15 or be adjusted to nRF54LM20A flash limits
- whether RTC, PDM mic, ADC, PWM, BLE, and PMIC-related features should be enabled by default
- whether any sensor or PMIC node from board DTS must be surfaced via overlay to keep examples functional

### Phase C. Ensure MicroPython build compatibility

Goals:

- build `lib/micropython/ports/zephyr` for `xiao_nrf54lm20a/nrf54lm20a/cpuapp`
- validate sysbuild behavior and generated hex outputs

Primary build command template:

```powershell
$env:PROJECT_DIR = "D:\workspace\micropython_seeed_board\micropython-seeed-boards"
west build .\lib\micropython\ports\zephyr --pristine --board xiao_nrf54lm20a/nrf54lm20a/cpuapp --sysbuild -- -DBOARD_ROOT=$env:PROJECT_DIR -DEXTRA_DTC_OVERLAY_FILE=$env:PROJECT_DIR\boards\xiao_nrf54lm20a_nrf54lm20a_cpuapp.overlay -DPM_STATIC_YML_FILE=$env:PROJECT_DIR\boards\pm_static_xiao_nrf54lm20a_nrf54lm20a_cpuapp.yml -DEXTRA_CONF_FILE=$env:PROJECT_DIR\boards\xiao_nrf54lm20a_nrf54lm20a_cpuapp.conf
```

If build fails, debug in this order:

1. board discovery / `BOARD_ROOT`
2. DTS include resolution
3. Kconfig symbol availability
4. partition conflicts
5. unsupported MicroPython Zephyr config in current submodule revision
6. custom module integration

Submodule rule:

- changes inside `lib/micropython` are allowed when necessary, but every such change must be documented in the progress log here and committed from the parent repo with the submodule pointer update.

### Phase D. Add Python board abstraction

Goals:

- make the examples layer work on `xiao_nrf54lm20a`

Required work:

- add `example/boards/xiao_nrf54lm20a.py`
- update `example/boards/xiao.py` to detect the new machine string
- encode pin / adc / pwm / i2c / spi / uart / pdm mappings from the imported board DTS

Initial mapping candidates from current Zephyr board definition:

- user UARTs:
  - `uart20` on P1.11 / P1.10
  - `uart21` on P1.8 / P1.9
- I2C:
  - `i2c22` on P1.3 / P1.7
  - `i2c30` on P0.8 / P0.7
- SPI:
  - `spi23` on P1.4 / P1.6 / P1.5
- PDM:
  - `pdm20` on P1.13 / P1.14
- RGB LEDs:
  - P1.22 / P1.23 / P1.24

These mappings must be validated against the XIAO connector semantics before finalizing the Python board map.

### Phase E. Flash tooling and package generation

Goals:

- create a `tools/xiao_nrf54lm20a_flash/` package parallel to `xiao_nrf54l15_flash`
- produce a distributable zip users can run directly on Windows

Required artifacts:

- flashing Python script
- Windows `.bat`
- Linux/macOS `.sh`
- final board hex
- merged sysbuild hex if required by the flashing flow

Validation requirements:

- auto-detect `.hex` behavior must still be deterministic
- target override / memory range / mass erase logic must match `nrf54lm20a`
- the tool must handle the normal single-probe case without extra arguments

### Phase F. Runtime validation

Minimum validation target:

- firmware flashes successfully
- board enumerates a usable serial interface
- MicroPython REPL is reachable
- `example/blink.py` works after copying `example/boards`
- at least one test each for GPIO, ADC, I2C, PWM, and filesystem

Stretch validation:

- PDM microphone
- BLE
- RTC
- battery / PMIC dependent examples

### Phase G. Documentation and release packaging

Deliverables:

- updated `README.md` build and flash instructions
- any board-specific notes needed for users
- final firmware archive analogous to `xiao54_flash`

Archive target shape:

- `xiao_nrf54lm20a_flash/flash.bat`
- `xiao_nrf54lm20a_flash/xiao_nrf54lm20a.hex`
- `xiao_nrf54lm20a_flash/merged.hex` if sysbuild generates and the flasher expects it
- `xiao_nrf54lm20a_flash/xiao_nrf54lm20a_flash.py`
- optional `README.txt` if the workflow differs materially from `xiao_nrf54l15`

## 9. Acceptance Criteria

The port is not complete until all conditions below are satisfied:

1. `west build` succeeds for `xiao_nrf54lm20a/nrf54lm20a/cpuapp` from this repository.
2. The produced image can be flashed from the packaged flasher directory on Windows.
3. The device boots to a working MicroPython REPL.
4. `example/boards/xiao.py` correctly resolves the new board.
5. `example/boards/xiao_nrf54lm20a.py` exposes correct mappings for the supported features.
6. At least the core examples needed for user confidence are validated: blink, gpio, adc, pwm, i2c/filesystem.
7. A compressed firmware package ready for end users exists in repository output workflow.
8. `AGENT.md` progress log reflects the meaningful implementation steps.

## 10. Execution Conventions

For every implementation cycle:

1. Inspect current state.
2. Make one coherent change.
3. Validate with the smallest relevant build/test step.
4. Update the progress log below.
5. Commit immediately.

Commit message style:

- `feat(nrf54lm20a): import zephyr board definition`
- `feat(nrf54lm20a): add micropython build overlays`
- `fix(nrf54lm20a): correct cpuflpr dts include`
- `feat(nrf54lm20a): add flash packaging tool`

## 11. Risks To Track

- upstream `lib/micropython` Zephyr port may not fully support `nrf54lm20a` in the checked out revision
- Nordic toolchain / board runner naming may differ between `nrf54l15` and `nrf54lm20a`
- sysbuild merged output names may differ from the current flash script assumptions
- Python machine string may not match a simple `"nrf54lm20a"` substring
- Seeed examples may assume sensors or PMIC behavior that is not yet exposed in MicroPython
- openocd / pyOCD support for `nrf54lm20a` may lag behind `nrf54l15`

Each risk should be either closed with validation evidence or recorded with a concrete workaround before release.

## 12. Progress Log

- 2026-06-03: Investigated repository structure, existing `xiao_nrf54l15` implementation, `xiao54_flash` package layout, and external `xiao_nrf54lm20a` Zephyr board definition. Created branch `nrf54lm20a_support` from `origin/master` because no `main` branch exists in the current remote. Added this `AGENT.md` as the execution guide for the remaining automated adaptation work.
- 2026-06-03: Restored `lib/micropython` to the upstream PR `18030` Zephyr baseline required by this repository after finding the submodule worktree was not usable. Imported `boards/seeed/xiao_nrf54lm20a/` from the Seeed Zephyr board source, fixed the `cpuflpr.dts` common DTSI include typo, and added `pre_dt_board.cmake` to wire Seeed user C modules for MicroPython builds.
- 2026-06-03: Added the first MicroPython-specific `xiao_nrf54lm20a` build override set: `cpuapp.conf`, `cpuapp.overlay`, and static partition layout. The first-pass configuration enables SPI/ADC/PDM/PWM/BLE/flash/filesystem support and defers RTC alias wiring until a valid `xiao_nrf54lm20a` RTC device mapping is confirmed.
- 2026-06-03: Root-caused the first real `west build` failure to a Zephyr/NCS compatibility mismatch: the imported board DTS referenced `nrf54lm20a_enga_*` SoC include files that do not exist in NCS `v3.3.0`. Updated the board to use the SoC DTS names actually present in the current workspace: `nrf54lm20a_cpuapp.dtsi` and `nrf54lm20a_cpuflpr.dtsi`.
- 2026-06-03: Root-caused the next `west build` failure to outdated board Kconfig symbol names. Updated `boards/seeed/xiao_nrf54lm20a/Kconfig.xiao_nrf54lm20a` to select `SOC_NRF54LM20A_CPUAPP` and `SOC_NRF54LM20A_CPUFLPR`, matching the symbols provided by NCS `v3.3.0`.
- 2026-06-03: Advanced the build past DTS, Kconfig, and Partition Manager. Root-caused the next failure to NCS boot-banner code still including legacy `<version.h>` while the MicroPython Zephyr port disables `CONFIG_LEGACY_GENERATED_INCLUDE_PATH`. Enabled the legacy generated include path in the `xiao_nrf54lm20a` extra board config as a compatibility workaround for the current NCS `v3.3.0` integration.
- 2026-06-03: Root-caused the next build breakage to Windows-host incompatibilities in `lib/micropython/py/mkrules.cmake`: Unix `touch` commands and shell pipeline preprocessing used by qstr generation. Replaced `touch` with `cmake -E touch` and added `lib/micropython/py/makeqstrdefs_preprocessed.py` to perform the qstr preprocessing step without relying on `cat`/`sed` shell tools.
- 2026-06-03: Validated a full `west build` for `xiao_nrf54lm20a/nrf54lm20a/cpuapp` using the current NCS `v3.3.0` workspace after fixing Zephyr 4.3 Bluetooth advertising option macro drift in `lib/micropython/ports/zephyr/modbluetooth_zephyr.c`. Successful outputs include `zephyr.elf`, `zephyr.hex`, `zephyr.bin`, and sysbuild `merged.hex`. The remaining work is now user-facing packaging and Python board mapping, not base board bring-up.
- 2026-06-03: Added `example/boards/xiao_nrf54lm20a.py` and updated `example/boards/xiao.py` so the repository-level Python helper layer can resolve `xiao_nrf54lm20a` machine strings and expose `Pin`/`ADC`/`PWM`/`I2C`/`SPI`/`UART`/`PDM` mappings for user examples.
- 2026-06-03: Created `tools/xiao_nrf54lm20a_flash/` with a user-facing pyOCD flashing script, platform launcher scripts, and a `flash.bat` entrypoint aligned with the existing `xiao54_flash` delivery pattern. The folder is intended to be populated with the freshly built `merged.hex` and board hex for end-user distribution.
- 2026-06-03: Updated `README.md` with `xiao_nrf54lm20a` build and flash commands, copied the successfully generated `merged.hex` and board hex into `tools/xiao_nrf54lm20a_flash/`, and prepared the repository for final archive packaging.
- 2026-06-03: Added `example/test_receiver.py`, a simple MicroPython command receiver that loops on `input()` and runs board smoke tests for LED, button, ADC, PWM, I2C scan, IMU presence, and PDM capture before returning to the receiver prompt.
- 2026-06-04: Compared the working `platform-seeedboards` flashing flow with the MicroPython flasher and found the key mismatch: the PlatformIO-side NRF uploader forces a forked pyOCD (`StarSphere-1024/pyOCD@lm20_stable`) and uses the explicit `nrf54lm20a` target instead of the generic `nrf54l` target. Updated `tools/xiao_nrf54lm20a_flash/xiao_nrf54lm20a_flash.py` to mirror that behavior.
- 2026-06-04: Root-caused the next flashing failure (`target was not halted as expected after calling flash algorithm routine (IPSR=3)`) to the remaining implementation difference between the two schemes: MicroPython was still using a custom pyOCD Python API path (`ConnectHelper` + `FileProgrammer`), while `platform-seeedboards` uses the `python -m pyocd flash ...` CLI directly. Replaced the custom API-based flasher with a thin wrapper around the proven CLI workflow.
- 2026-06-04: Further aligned the CLI arguments with `platform-seeedboards`. Removed extra `--connect under-reset`, `--erase chip`, and explicit `--format hex` options so the MicroPython flasher now follows the same minimal `pyocd flash --target nrf54lm20a --frequency 4000000 <hex>` command shape as the working platform uploader.
- 2026-06-04: Confirmed that `platform-seeedboards` defaults to `cmsis-dap` (OpenOCD), not pyOCD, for `seeed-xiao-nrf54lm20a`. After verifying that the pyOCD target file already programs the expected RRAM control registers, concluded that the remaining `IPSR=3` failure is inside pyOCD's program-page path rather than a missing wrapper-side register write. Switched the MicroPython flasher to use OpenOCD by default, with pyOCD retained as an optional backend for diagnostics.
- 2026-06-04: Made the OpenOCD-based flashing package self-contained by bundling `openocd.cfg` into `tools/xiao_nrf54lm20a_flash/` and updating the flasher to prefer the local config path. This fixes validation failures caused by unpacking the firmware archive outside the repository tree.
- 2026-06-04: Verified locally that the self-contained OpenOCD flow exits with code `0` and that `verify_image` succeeds even though OpenOCD still prints `double fault` / `HardFault` messages during the erase-recovery sequence. Updated the flasher to run `verify_image` explicitly and emit a final success message so validation can key off the real success condition instead of those intermediate warnings.
