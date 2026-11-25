"""Sample the SteamVR HMD pose alongside a UDP pcapng capture."""
import argparse
import json
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).with_name('.deps')))


def main():
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, signal.default_int_handler)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", help="new JSON Lines output file")
    parser.add_argument("--rate", type=float, default=90, help="sampling rate in Hz (default: 90)")
    args = parser.parse_args()
    if not 1 <= args.rate <= 1000:
        parser.error("--rate must be between 1 and 1000")
    try:
        import openvr
    except ImportError:
        parser.error("Python package openvr is required: python -m pip install openvr")

    # Exclusive creation avoids overwriting another recording.
    with open(args.output, "x", encoding="utf-8", buffering=1) as output:
        initialized = False
        try:
            system = openvr.init(openvr.VRApplication_Utility)
            initialized = True
            output.write(json.dumps({"type": "header", "version": 1,
                                     "source": "OpenVR", "origin": "standing",
                                     "rate_hz": args.rate}) + "\n")
            print("Recording HMD poses; press Ctrl+C to stop.", flush=True)
            interval = 1.0 / args.rate
            deadline = time.monotonic()
            while True:
                before_ns = time.time_ns()
                poses = system.getDeviceToAbsoluteTrackingPose(
                    openvr.TrackingUniverseStanding, 0.0, openvr.k_unMaxTrackedDeviceCount
                )
                after_ns = time.time_ns()
                pose = poses[openvr.k_unTrackedDeviceIndex_Hmd]
                matrix = pose.mDeviceToAbsoluteTracking.m
                record = {
                    "type": "pose", "time_unix_ns": (before_ns + after_ns) // 2,
                    "query_duration_ns": after_ns - before_ns,
                    "connected": bool(pose.bDeviceIsConnected),
                    "valid": bool(pose.bPoseIsValid),
                    "tracking_result": int(pose.eTrackingResult),
                    "matrix_3x4": [[float(matrix[r][c]) for c in range(4)] for r in range(3)],
                    "velocity": [float(pose.vVelocity.v[i]) for i in range(3)],
                    "angular_velocity": [float(pose.vAngularVelocity.v[i]) for i in range(3)],
                }
                output.write(json.dumps(record, separators=(",", ":"), allow_nan=False) + "\n")
                deadline += interval
                now = time.monotonic()
                if deadline < now:
                    deadline = now
                time.sleep(max(0, deadline - now))
        except KeyboardInterrupt:
            print("Recording stopped.")
        finally:
            if initialized:
                openvr.shutdown()


if __name__ == "__main__":
    main()
