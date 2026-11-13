# πRemote for Windows

Extract the whole folder. Run **πRemote.exe**. Enter the Force IP and click **CONNECT**. The same button becomes green **DISCONNECT**. Pin keeps the panel above the official Akai Remote Screen.

Requires Windows 10/11, .NET Framework 4.8, WSL Ubuntu with Python 3/OpenSSH, and the standalone πRemote addin installed on the Force. No Commander app or addin is required.

Keep these files together: `πRemote.exe`, `πRemote.exe.config`, `piRemote.ico`, `connect.py`, `Activate-Force.ps1`, `Force-IP.txt`. The config enables sharp per-monitor DPI rendering. The folder needs write access to remember the IP.

## SSH setup

From WSL Ubuntu, connect to the Force normally once and verify its SSH host fingerprint. Configure SSH key authentication. The app intentionally does not carry keys, passwords or device fingerprints and does not accept an unknown host key automatically.

The official Remote Screen remains a separate app. Its Scale button switches between fit-to-window and native 1:1 display.

## Inactive addin

After a Force reboot, CONNECT may report that the installed addin is inactive. It offers activation with a clear save-project warning. If accepted, it calls its WSL/SSH helper directly to re-register the addin and restart MPC. It does not require Windows PowerShell script execution. A small service-configuration backup is kept in WSL's private `~/.cache/piremote` folder first.

If PowerShell blocks a downloaded script, review the archive and its origin, then use Windows Properties → Unblock on the ZIP before extracting, according to your local policy. The app does not change execution policy.

Optional PowerShell script (when your policy allows local scripts); the app itself does not need it:

```powershell
& '.\Activate-Force.ps1' -ForceIP 'YOUR_FORCE_IP'
```

It asks you to type YES after saving. No automatic activation occurs in the connection tests.

## Controls

- PLAY: green while inferred playing; STOP clears PLAY/REC.
- REC: rose red when record is armed; press PLAY if stopped.
- SHIFT/EDIT: apply once to the next hardware shortcut.
- EDIT PLUGIN: EDIT + the last selected track button.
- 01–08 / 09–16: request a bank change in Matrix. Track state is local; verify it after using the Force itself. The second bank still needs a device test with enough tracks.

Transport colours follow physical button events, not the audio engine. Clicking touchscreen transport controls may not update them. Disconnect stops the connection, not playback on the Force.

No transport/navigation commands are sent on connecting or reconnecting. Disconnect releases held navigation keys and closes only this app's SSH tunnel.

This exact candidate is offline-tested; real-device installation/reboot tests are pending.
