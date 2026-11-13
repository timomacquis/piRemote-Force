# πRemote — Force installation

**Candidate 0.1.0. Force Gen1 / ARM32, MPC OS 3.10.1. Not for Gen2.**

This addin supplies transport and physical-button navigation for the πRemote Windows app. The official Akai Remote Screen continues to supply video, touch and audio. Commander is not required.

## Install

Save the project first. Extract this ZIP on the Force, open SSH, enter the extracted folder and run:

```sh
sh install.sh
```

The standard installer copies the library and configuration to `/data/mpc-addins/piremote`, preserves other preload libraries and restarts MPC after confirmation.

For a batch install without an immediate restart:

```sh
sh install.sh -y -n
```

It takes effect only after MPC is restarted. Do not overwrite a live library by hand; the installer stages it safely.

## After a full reboot

Persistence depends on the actual overlay and bootstrap configuration. The current standard installer knows stacked writable overlays under a read-only `/etc`; on systems where it cannot persist, it uses `/run` and reports that limitation.

If πRemote is installed but inactive, the Windows CONNECT button offers to run its PowerShell activation script. Confirm only after saving the project: activation restarts MPC.

Manual equivalent on the Force, after saving:

```sh
sh /data/mpc-addins/piremote/install.sh -y -n -t /data/mpc-addins/piremote
systemctl restart acvs
```

No reboot test of this exact package has been completed yet.

## Network

The server listens on **127.0.0.1:6732**. The Windows app opens its own SSH tunnel on local port **16732**. It does not close the official viewer or Commander tunnels.

`piremote.conf` contains `enabled=1`, `bind=127.0.0.1`, `port=6732`. Keep the default bind. Using `0.0.0.0` exposes unauthenticated transport and hardware-button control to your network.

The server has no video, audio or file-access endpoints. It does not collect or list projects/plugins.

## Remove or recover

After saving the project:

```sh
sh /data/mpc-addins/piremote/uninstall.sh
```

If MPC fails to start, SSH remains available. Stop MPC, remove only πRemote, then start MPC again:

```sh
systemctl stop acvs
sh /data/mpc-addins/piremote/uninstall.sh -y -n
systemctl daemon-reload
systemctl start acvs
```

Do not delete other addins or replace their service configuration.

## Prototype migration

This package does not silently remove Commander or the earlier experimental navigation bridge. A real-device migration must remove only the earlier πRemote trial overrides after backing them up. The prototype and this addin share raw-input hooks; simultaneous operation is not yet device-qualified. Keep the working prototype until the new package has been tested.
