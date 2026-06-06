import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.music import (load, notes_to_midi, ql, note_on, build_track,
                       write_midi, out_path, expand_drum_pattern)

def chord_track(d):
    bar = ql(d["beats_per_chord"])
    ev = []
    t = 0
    for chord in d["progression"]:
        for m in notes_to_midi(chord["notes"]):
            note_on(ev, t, m, bar, d["velocity"])
        t += bar
    return build_track(ev, "Jazz Chords", tempo_bpm=d["tempo"])

def drum_track(d, n_bars):
    bar_ticks = ql(4)   # 4/4
    dd = d["drums"]
    ev = expand_drum_pattern(
        dd, n_bars, bar_ticks,
        swing_ticks=dd.get("swing_ticks", 0),
    )
    return build_track(ev, "Jazz Drums")

if __name__ == "__main__":
    d = load("jazz_with_drums")
    n_bars = len(d["progression"])
    write_midi(out_path("jazz_with_drums.mid"), [chord_track(d), drum_track(d, n_bars)])
    print(f"wrote jazz_with_drums.mid — {n_bars} bars + swing drums")
    print("tracks: 1) Jazz Chords  2) Jazz Drums")
