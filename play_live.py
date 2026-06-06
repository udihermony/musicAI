"""Stream any .mid file live to GarageBand over the IAC Driver — no exporting.

    .venv/bin/python play_live.py jazz_electronic.mid           # play once
    .venv/bin/python play_live.py jazz_electronic.mid --loop     # loop until Ctrl+C
    .venv/bin/python play_live.py jazz_electronic.mid -i 4       # 4-second lead-in

Enable the IAC Driver in Audio MIDI Setup (MIDI Studio -> IAC Driver -> "Device
is online"), then set GarageBand tracks to record-enable / monitor that input.
mido handles tempo and per-track timing, so all four tracks play together with
their real rhythms (including drums on channel 10).
"""

import argparse
import sys
import time

import mido


def pick_iac_port() -> str:
    outputs = mido.get_output_names()
    if not outputs:
        sys.exit("no MIDI outputs found — enable IAC Driver in Audio MIDI Setup")
    for name in outputs:
        if "IAC" in name or "Bus" in name:
            return name
    print(f"no IAC port found; falling back to {outputs[0]!r}")
    return outputs[0]


def all_notes_off(out) -> None:
    """Panic: silence every channel so nothing hangs on stop/Ctrl+C."""
    for ch in range(16):
        out.send(mido.Message("control_change", control=123, value=0, channel=ch))


def play(path: str, port_name: str, lead_in: float = 0.0, loop: bool = False) -> None:
    mid = mido.MidiFile(path)
    print(f"sending {path} ({mid.length:.1f}s) to: {port_name}")
    if lead_in > 0:
        for s in range(int(lead_in), 0, -1):
            print(f"  starting in {s}...")
            time.sleep(1)

    with mido.open_output(port_name) as out:
        try:
            pass_no = 0
            while True:
                pass_no += 1
                if loop:
                    print(f"  pass {pass_no} (Ctrl+C to stop)")
                for msg in mid.play():          # yields in real time, tempo-aware
                    if not msg.is_meta:
                        out.send(msg)
                if not loop:
                    break
        except KeyboardInterrupt:
            print("\n  stopped")
        finally:
            all_notes_off(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Stream a .mid file live to IAC.")
    ap.add_argument("midifile", help="path to the .mid file to play")
    ap.add_argument("--loop", action="store_true", help="repeat until Ctrl+C")
    ap.add_argument("-i", "--lead-in", type=float, default=0.0,
                    help="seconds to count in before playing")
    args = ap.parse_args()

    play(args.midifile, pick_iac_port(), lead_in=args.lead_in, loop=args.loop)
    print("done")
