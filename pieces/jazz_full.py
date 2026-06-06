import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.music import (load, note_to_midi, notes_to_midi, ql, note_on,
                       build_track, write_midi, out_path, expand_drum_pattern)

def chord_track(d, loops):
    bar = ql(d["beats_per_chord"])
    ev = []
    t = 0
    for _ in range(loops):
        for chord in d["progression"]:
            for m in notes_to_midi(chord["notes"]):
                note_on(ev, t, m, bar, d["velocity"])
            t += bar
    return build_track(ev, "Jazz Chords", tempo_bpm=d["tempo"])

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
                m = note_to_midi(pitch)
                note_on(ev, t, m, note_dur, vel, ch=1)
                t += beat
    return build_track(ev, "Walking Bass")

def drum_track(d, n_bars):
    dd = d["drums"]
    ev = expand_drum_pattern(dd, n_bars, ql(4), swing_ticks=dd.get("swing_ticks", 0))
    return build_track(ev, "Jazz Drums")

if __name__ == "__main__":
    d = load("jazz_full")
    loops = d["loops"]
    n_bars = loops * len(d["progression"])
    tracks = [chord_track(d, loops), bass_track(d, loops), drum_track(d, n_bars)]
    write_midi(out_path("jazz_full.mid"), tracks)
    print(f"wrote jazz_full.mid — {loops} loops × {len(d['progression'])} bars = {n_bars} bars")
    print("tracks: 1) Jazz Chords  2) Walking Bass  3) Jazz Drums")
