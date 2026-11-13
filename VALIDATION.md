# Validation — πRemote 0.1.0

## Confirmed on Force — 13 November 2026

- The user installed the standalone addin and reported that it was tested and works very well with the Windows companion.
- Device: Akai Force Gen1, MPC OS 3.10.1.12.
- Running addin SHA-256: `04ec7b951aeb81065116cf1a3c7270d0599aa83dbb225be77e6678c310f137da`, identical to the release library.
- The endpoint reported product piremote, version 0.1.0, ready=true.
- Process maps contained piRemote and File Browser, without Commander or the old navigation bridge.
- A full reboot was independently observed: the kernel boot ID changed, MPC became active and piRemote became ready without a PC activation command. The Windows app had been closed.
- The user selected the validated automatic-startup behaviour for publication. An on-demand-only mode is not part of this release.

## Passed offline

- ARMv7 hard-float build; ELF32/ARM and imported glibc symbols checked (maximum 2.34, target Force 3.10.1).
- ASan/UBSan command parser, allowlist, HTTP bounds/Host/Origin checks, transport queue and release watchdog tests.
- Real HTTP service inside a fake MPC process with fake raw MIDI; accepted transport/navigation reaches the process input. Invalid pad messages are rejected.
- Upstream surface tests preserve partial messages, SysEx boundaries, hardware running status and poll wakeup.
- Activation arguments support spaces and Unicode paths; activation without saved-project confirmation is rejected. The optional PowerShell path conversion is tested with a mock WSL function.
- The native Windows app self-test checks layout, colours, protocol formatting and activation guards.
- The real Windows app connects, disconnects and reconnects to the standalone fake server. The fake hardware capture remains empty during those connection tests.
- The packaged standard installer/uninstaller passes in a disposable systemd tree, preserving another addin and touching no real service.
- `catalog_check.py --catalog`: OK. Expected warnings: GLIBC 2.34 (OS 3.x only) and networking for manual review. The package targets Force 3.10.1 and binds to localhost by default.

## Remaining scope

- A separately recorded real-device uninstall/reinstall log is not claimed; the automated package lifecycle test is offline.
- The 09–16 bank and 08/09 boundary need a dedicated test with enough tracks. Track selection is local to the remote, not a live host project selection readout.
- Transport indicators follow button events, not audio-engine telemetry; individual shortcut semantics and simultaneous physical use can receive further testing.
- The inactive-addin recovery offer is tested offline; its real WSL/SSH/MPC restart path is a separate device check.
- No CPU benchmark or catalogue Verified tier is claimed. The requested initial listing is Listed.

The earlier Commander-backed prototype's tests are retained as historical context, not substituted for the independent build's evidence. Private device logs and boot identifiers remain local; the public record contains no personal IP address or SSH key.