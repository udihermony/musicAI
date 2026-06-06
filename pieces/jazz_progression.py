import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.music import load, note_to_midi, notes_to_midi, ql, note_on, build_track, write_midi, out_path

def make(d):
    tpb = 480
    bar = ql(d["beats_per_chord"])
    vel = d["velocity"]
    ev = []
    t = 0
    for chord in d["progression"]:
        for m in notes_to_midi(chord["notes"]):
            note_on(ev, t, m, bar, vel)
        t += bar
    track = build_track(ev, "Jazz Chords", tempo_bpm=d["tempo"])
    return [track]

if __name__ == "__main__":
    d = load("jazz_progression")
    write_midi(out_path("jazz_progression.mid"), make(d))
    names = " → ".join(c["name"] for c in d["progression"])
    print(f"wrote jazz_progression.mid — {names} @ {d['tempo']} BPM")
    print("drag into GarageBand and assign a Software Instrument.")
