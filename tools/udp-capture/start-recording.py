"""Launch receiver HID and OpenVR HMD recordings together on Windows."""
import datetime
import importlib.util
import msvcrt
from pathlib import Path
import signal
import subprocess
import sys
import time


def main():
    sys.path.insert(0, str(Path(__file__).with_name(".deps")))
    if importlib.util.find_spec("openvr") is None:
        raise RuntimeError("Install the OpenVR binding first: python -m pip install openvr")
    if importlib.util.find_spec("hid") is None:
        raise RuntimeError("Install hidapi first: python -m pip install hidapi")
    directory = Path.cwd() / ("slime-recording-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    directory.mkdir(exist_ok=False)
    print("Saving to:", directory, "\nReceiver: VID 1209 PID 7690", flush=True)
    children = []
    try:
        hmd = subprocess.Popen([sys.executable, str(Path(__file__).with_name("record-hmd.py")),
                                str(directory / "headset.jsonl")],
                               creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        children.append(hmd)
        capture = subprocess.Popen([sys.executable, str(Path(__file__).with_name("record-hid.py")),
                                    str(directory / "receiver.jsonl")],
                                   creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        children.append(capture)
        print("Press Enter to stop both recordings.", flush=True)
        while True:
            for child in children:
                if child.poll() is not None:
                    raise RuntimeError(f"A recorder exited early (code {child.returncode}). Check its output.")
            if msvcrt.kbhit() and msvcrt.getwch() in ("\r", "\n"):
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        for child in children:
            if child.poll() is None:
                try:
                    child.send_signal(signal.CTRL_BREAK_EVENT)
                except OSError:
                    child.terminate()
        for child in children:
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
                print("A recorder did not stop gracefully; verify its output file.")
    print("Finished. Check both files and the HID report count.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        print("Recording failed:", error, file=sys.stderr)
        sys.exit(1)
