"""Jazz-electronic piece. All musical content lives in data/jazz_electronic.yaml."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.music import (load, note_to_midi, notes_to_midi, ql, note_on,
                       build_track, write_midi, out_path, expand_drum_pattern)

S = 480 // 4   # one sixteenth in ticks

def keys_events(d):
    bar  = ql(4)
    comp = [(c[0], c[1]) for c in d["patterns"]["keys_comp"]]
    ch   = d["channels"]["keys"]
    ev   = []
    for i, chord in enumerate(d["chords"]):
        base    = i * bar
        voicing = notes_to_midi(chord["voicing"])
        if chord["style"] == "drone":
            for m in voicing:
                note_on(ev, base, m, bar, 70, ch=ch)
        else:
            for start, dur in comp:
                vel = 78 if start == 0 else 68
                for m in voicing:
                    note_on(ev, base + start, m, dur, vel, ch=ch)
    return ev

def bass_events(d):
    bar = ql(4)
    fig = d["patterns"]["bass_figure"]
    ch  = d["channels"]["bass"]
    ev  = []
    for i, chord in enumerate(d["chords"]):
        base = i * bar
        root = note_to_midi(chord["bass"])
        if chord["style"] == "drone":
            note_on(ev, base, root, bar, 88, ch=ch)
        else:
            for pos, length, octv in fig:
                vel = 100 if pos == 0 else 84
                note_on(ev, base + pos * S, root + octv, length * S, vel, ch=ch)
    return ev

def arp_events(d):
    bar   = ql(4)
    step  = d["patterns"]["arp_step_ticks"]
    dur   = d["patterns"]["arp_note_dur_ticks"]
    total = len(d["chords"]) * bar
    ch    = d["channels"]["arp"]
    ev    = []
    t = idx = 0
    while t < total:
        i = min(t // bar, len(d["chords"]) - 1)
        voicing = notes_to_midi(d["chords"][i]["voicing"])
        pool    = voicing + [voicing[0] + 12, voicing[1] + 12]
        vel     = 90 if t % bar == 0 else 74
        note_on(ev, t, pool[idx % len(pool)], min(dur, total - t), vel, ch=ch)
        idx += 1
        t   += step
    return ev

if __name__ == "__main__":
    d     = load("jazz_electronic")
    n     = len(d["chords"])
    ch    = d["channels"]
    pr    = d["programs"]
    fill  = d["drums"].get("fill", {})
    drums = expand_drum_pattern(
        d["drums"], n, ql(4),
        swing_ticks=d["drums"]["swing_ticks"],
        fill_every=fill.get("every_n_bars"),
        fill_notes=fill or None,
    )
    tracks = [
        build_track(keys_events(d), "Rhodes",     pr["keys"], ch["keys"], tempo_bpm=d["tempo"]),
        build_track(bass_events(d), "Synth Bass", pr["bass"], ch["bass"]),
        build_track(arp_events(d),  "Poly Arp",   pr["arp"],  ch["arp"]),
        build_track(drums,          "Drums",       channel=ch["drums"]),
    ]
    write_midi(out_path("jazz_electronic.mid"), tracks)
    print(f"wrote jazz_electronic.mid — {n} bars of 4/4 at {d['tempo']} BPM (A/B form)")
    print(f"  A: {' '.join(c['name'] for c in d['chords'][:8])}")
    print(f"  B: {' '.join(c['name'] for c in d['chords'][8:])}")
    print("tracks: 1) Rhodes  2) Synth Bass  3) Poly Arp  4) Drums")
