"""Record SlimeVR receiver HID reports without modifying the server."""
import argparse
import collections
import json
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).with_name('.deps')))


def main():
    if hasattr(signal, 'SIGBREAK'):
        signal.signal(signal.SIGBREAK, signal.default_int_handler)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output')
    parser.add_argument('--duration', type=float, default=0, help='seconds; 0 means until Ctrl+C')
    args = parser.parse_args()
    if args.duration < 0:
        parser.error('duration must not be negative')
    try:
        import hid
    except ImportError:
        parser.error('Install hidapi: python -m pip install hidapi')
    devices = hid.enumerate(0x1209, 0x7690)
    if len(devices) != 1:
        raise RuntimeError(f'Expected one receiver HID interface, found {len(devices)}')
    device = hid.device()
    device.open_path(devices[0]['path'])
    start = time.monotonic()
    counts = collections.Counter()
    lengths = collections.Counter()
    reports = 0
    try:
        with open(args.output, 'x', encoding='utf-8', buffering=1) as output:
            output.write(json.dumps({'type': 'header', 'version': 1, 'vid': 0x1209,
                                     'pid': 0x7690, 'serial': devices[0]['serial_number']}) + '\n')
            try:
                while not args.duration or time.monotonic() - start < args.duration:
                    data = bytes(device.read(64, 100))
                    if not data:
                        continue
                    output.write(json.dumps({'type': 'report', 'time_unix_ns': time.time_ns(),
                                             'hex': data.hex()}, separators=(',', ':')) + '\n')
                    reports += 1
                    lengths[len(data)] += 1
                    if len(data) % 16 == 0:
                        counts.update(data[i] for i in range(0, len(data), 16))
            except KeyboardInterrupt:
                pass
    finally:
        device.close()
    print('Reports:', reports, 'lengths:', dict(lengths), '16-byte packet types:', dict(counts), flush=True)
    if not reports:
        raise RuntimeError('No HID reports received; recording is empty.')


if __name__ == '__main__':
    main()
