# FreeRDP bug report — draft (issue #38)

**Titre proposé** : `serial/parallel client channels announce a non-empty DeviceData, rejected by FreeRDP's own rdpdr server (MS-RDPESP requires 0)`

**Dépôt cible** : https://github.com/FreeRDP/FreeRDP/issues

## Corps du rapport (anglais)

### Description

The serial and parallel client channel plugins write the device name followed by a NUL byte into the `DeviceData` field of the `DEVICE_ANNOUNCE` header (`DR_CORE_DEVICELIST_ANNOUNCE_REQ`), while the rdpdr **server** channel of FreeRDP itself rejects any serial/parallel announcement with `DeviceDataLength != 0` (`ERROR_INVALID_DATA`), so a FreeRDP client announcing serial/parallel ports against a FreeRDP server fails with no device created.

We found this while running a third-party client against FreeRDP's example server (rdpdr server channel): serial (`COM3`) and parallel (`LPT1`) announcements were systematically rejected, server log:

```
[WARN][...rdpdr.server] - [rdpdr_server_receive_device_list_announce_request]:
    [rdpdr] RDPDR_DTYP_SERIAL::DeviceDataLength != 0 [5]
    [rdpdr] RDPDR_DTYP_PARALLEL::DeviceDataLength != 0 [5]
```

Reading the FreeRDP sources, the two halves disagree:

- `channels/serial/client/serial_main.c` and `channels/parallel/client/parallel_main.c` allocate the announce `DeviceData` as `Stream_New(nullptr, len + 1)` and write the device name byte-by-byte followed by NUL (5 bytes for `COM3`), which `channels/rdpdr/client/rdpdr_main.c` serializes as-is.
- `channels/rdpdr/server/rdpdr_main.c` requires `DeviceDataLength == 0` for `RDPDR_DTYP_SERIAL` / `RDPDR_DTYP_PARALLEL` and answers `ERROR_INVALID_DATA` otherwise (no `DR_CORE_DEVICE_ANNOUNC_RSP` success / no `CREATE` callback).

### Expected behavior

Per **[MS-RDPESP] section 2.2.2.1** (Client Device List Announce Request, port redirection):

> DeviceDataLength: Number of bytes in the DeviceData field. **For port devices, this value is set to 0.**

The port name belongs in `PreferredDosName` (8 bytes, NUL-terminated, max 7 characters), not in `DeviceData`. So the **server-side check is spec-correct** and the **client serial/parallel channels are the offender**: they should announce with `DeviceDataLength = 0` (and their device-name writing either dropped or moved to `PreferredDosName` handling).

### Reproduction

- Run FreeRDP's example server with the rdpdr server channel (generic RDPDR server).
- Connect a client whose announce for a serial port yields `DeviceDataLength = 5` (name `COM3` + NUL) — this is what FreeRDP's own `serial` client channel produces.
- Server rejects both serial and parallel announcements (`ERROR_INVALID_DATA`), printer and drive announcements succeed.

### Environment

- FreeRDP channels involved: `rdpdr` (client + server), `serial` (client), `parallel` (client)
- Observed with FreeRDP master sources as of 2026-09-16 (`channels/rdpdr/server/rdpdr_main.c`, `channels/serial/client/serial_main.c`, `channels/parallel/client/parallel_main.c`)

### Suggested fix

In `serial_main.c` / `parallel_main.c`, announce with `DeviceDataLength = 0` (keep the name in `PreferredDosName` only), matching [MS-RDPESP] 2.2.2.1 and the server-side validation that already exists.

## Historique interne

- Diagnostiqué le 2026-09-16 (session 29, docs/sessions/session-29.md) : sortie serveur identique sur trois exécutions ; `datalen=5` observé pour COM3/LPT1.
- Rapport rédigé le 20/10/2026 en vue du dépôt sur github.com/FreeRDP/FreeRDP (action de l'issue #38) — dépôt soumis à l'approbation de Mathilde avant publication.
