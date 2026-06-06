import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.music import load, note_to_midi, ql, note_on, build_track, write_midi, out_path

def melody_track(d):
    ev = []
    t = 0
    for entry in d["melody"]:
        pitch, dur_ql = entry
        dur = ql(dur_ql)
        m = note_to_midi(pitch)
        if m is not None:
            note_on(ev, t, m, dur, d["melody_velocity"])
        t += dur
    return build_track(ev, "Melody", tempo_bpm=d["tempo"],
                       time_sig=d["time_signature"])

def bass_track(d):
    ev = []
    t = 0
    for pitch, dur_ql in d["bass"]:
        note_on(ev, t, note_to_midi(pitch), ql(dur_ql), d["bass_velocity"], ch=1)
        t += ql(dur_ql)
    return build_track(ev, "Bass")

if __name__ == "__main__":
    d = load("fur_elise")
    write_midi(out_path("fur_elise.mid"), [melody_track(d), bass_track(d)])
    bars = sum(e[1] for e in d["melody"]) / 1.5   # 1.5 ql per 3/8 bar
    print(f"wrote fur_elise.mid — {bars:.0f} bars of 3/8 at {d['tempo']} BPM")
    print("tracks: 1) Melody  2) Bass")
    print("drag into GarageBand — assign piano to melody, upright bass or cello to bass.")
