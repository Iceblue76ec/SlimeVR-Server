# SlimeVR receiver and headset recorder (Windows)

Double-click `start-recording.cmd` with SteamVR and SlimeVR running. Press Enter
to stop. The timestamped output folder contains `receiver.jsonl` (raw HID
reports) and `headset.jsonl` (independent OpenVR pose samples). Install Python,
`hidapi`, and `openvr` first: `python -m pip install hidapi openvr`. A local
`.deps` installation of these packages is also supported. No Wireshark is needed.

The receiver is identified by USB VID 1209 and PID 7690; the recorder refuses
to choose if there is not exactly one matching HID interface. It opens a
separate HID handle and records each report's unmodified bytes as hex with a
Unix nanosecond timestamp. On this machine two seconds produced 52 reports of
64 bytes, including type 1 rotation packets. This is a second reader, not a
capture of what Server actually read; reports could be lost or delivered
differently. Verify simultaneous operation and report counts in your setup.

The headset file samples OpenVR standing-space transforms at about 90 Hz and
uses the same wall clock. It is not the exact SteamVR bridge input. Avoid clock
adjustments during recording. The two streams start and stop separately; use
their timestamps for alignment. Buttons, initial state, and server settings
are not recorded; replay is not implemented.

For a short HID-only test, use:

```powershell
python .\tools\udp-capture\record-hid.py .\receiver-test.jsonl --duration 2
```

The recorder does not capture USB transport events or server responses. HID
handles and file permissions may require administrative privileges. Check that
reports include your trackers' registration and rotation data, and retain the
initial server configuration if you need to investigate later. Files may
contain device identifiers; review them before sharing.
