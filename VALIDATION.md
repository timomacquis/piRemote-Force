# Validation — 0.1.0 preview

## Passed offline

- ARMv7 hard-float build; ELF32/ARM and imported glibc symbols checked (maximum 2.34, target Force 3.10.1).
- ASan/UBSan command parser, allowlist, HTTP bounds/Host/Origin checks, transport queue and release watchdog tests.
- Real HTTP service inside a fake MPC process with fake raw MIDI; accepted transport/navigation reaches the process input. Invalid pad messages are rejected.
- Upstream surface tests for poll wakeup, partial messages, SysEx boundaries and preserved hardware running status.
- Native Windows application self-test: four-slot layout, one 16 px CONNECT/DISCONNECT button, colours and protocol formatting.
- Native Windows app connects, disconnects and reconnects to the standalone fake server. The fake hardware capture remains empty: no transport/navigation commands are sent during those connection tests.
- Packaged standard installer/uninstaller passes in a disposable systemd tree, preserving another addin and touching no real service.
- `catalog_check.py --catalog`: OK. Expected warnings: GLIBC 2.34 (OS 3.x only) and network server for manual review. This package targets Force 3.10.1, binds to localhost by default and is accessed over SSH.

## Pending on the exact standalone package

- Saved-project device install/uninstall/reinstall.
- PLAY/STOP/REC semantics, observed button colours, navigation and EDIT + track on real hardware.
- Track groups 09–16 and the 08/09 boundary with enough tracks.
- Hardware controls still operate, including simultaneous physical use.
- Audio behaviour while operating the remote; no device CPU figure claimed.
- Full reboot and persistence under the actual 3.10.1 overlay.
- Windows activation offer and the real PowerShell/MPC restart path.

The previous Commander-backed prototype was validated for PLAY, STOP, MATRIX and EDIT + the first two track buttons. That result is retained as a reference, not counted as device validation of this independent binary. The proposed catalogue tier is Experimental.