import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.music import (load, note_to_midi, notes_to_midi, ql, note_on,
                       build_track, write_midi, out_path, expand_drum_pattern)

def chord_track(d, loops):
    ev = []
    t = 0
    for _ in range(loops):
        for chord in d["progression"]:
            dur = ql(chord.get("beats", 4))
            for m in notes_to_midi(chord["notes"]):
                note_on(ev, t, m, dur, d["velocity"])
            t += dur
    return build_track(ev, "Blues Chords", tempo_bpm=d["tempo"])

def bass_track(d, loops):
    wb = d["walking_bass"]
    gap = wb["note_gap"]
    vel = wb["velocity"]
    beat = ql(1.0)
    note_dur = beat - gap
    ev = []
    t = gap
    for _ in range(loops):
        for bar in wb["bars"]:
            for pitch in bar:
                note_on(ev, t, note_to_midi(pitch), note_dur, vel, ch=1)
                t += beat
    return build_track(ev, "Walking Bass")

def drum_track(d, n_bars):
    dd = d["drums"]
    ev = expand_drum_pattern(dd, n_bars, ql(4), swing_ticks=dd.get("swing_ticks", 0))
    return build_track(ev, "Jazz Drums")

if __name__ == "__main__":
    d = load("jazz_blues")
    loops = d["loops"]
    n_bars = loops * len(d["walking_bass"]["bars"])
    tracks = [chord_track(d, loops), bass_track(d, loops), drum_track(d, n_bars)]
    write_midi(out_path("jazz_blues.mid"), tracks)
    print(f"wrote jazz_blues.mid — F blues, 12 bars × {loops} loops = {n_bars} bars")
    print("tracks: 1) Blues Chords  2) Walking Bass  3) Jazz Drums")
