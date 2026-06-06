"""Jazz-electronic piece. All musical content lives in data/jazz_electronic.yaml."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.music import (load, note_to_midi, notes_to_midi, ql, note_on, cc,
                       build_track, write_midi, out_path, GM_DRUMS)

TPB = 480
S = TPB // 4          # one sixteenth note in ticks
DOTTED_8TH = 3 * S   # 360 — the arp pulse

def _bar_ticks(d):
    return ql(4)      # 4/4

def keys_events(d):
    chords = d["chords"]
    comp = [(c[0], c[1]) for c in d["patterns"]["keys_comp"]]
    bar = _bar_ticks(d)
    ev = []
    for i, chord in enumerate(chords):
        base = i * bar
        voicing = notes_to_midi(chord["voicing"])
        if chord["style"] == "drone":
            # sustained pad — ring the whole bar
            for m in voicing:
                note_on(ev, base, m, bar, 70, ch=d["channels"]["keys"])
        else:
            for start, dur in comp:
                vel = 78 if start == 0 else 68
                for m in voicing:
                    note_on(ev, base + start, m, dur, vel, ch=d["channels"]["keys"])
    return ev

def bass_events(d):
    chords = d["chords"]
    fig = d["patterns"]["bass_figure"]
    bar = _bar_ticks(d)
    ch = d["channels"]["bass"]
    ev = []
    for i, chord in enumerate(chords):
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
    chords = d["chords"]
    step = d["patterns"]["arp_step_ticks"]
    dur  = d["patterns"]["arp_note_dur_ticks"]
    bar  = _bar_ticks(d)
    total = len(chords) * bar
    ch = d["channels"]["arp"]
    ev = []
    t = 0
    idx = 0
    while t < total:
        i = t // bar
        if i >= len(chords):
            break
        voicing = notes_to_midi(chords[i]["voicing"])
        pool = voicing + [voicing[0] + 12, voicing[1] + 12]
        m = pool[idx % len(pool)]
        vel = 90 if t % bar == 0 else 74
        actual_dur = min(dur, total - t)
        note_on(ev, t, m, actual_dur, vel, ch=ch)
        idx += 1
        t += step
    return ev

def drum_events(d):
    chords = d["chords"]
    n_bars = len(chords)
    bar = _bar_ticks(d)
    dd = d["drums"]
    note_map = GM_DRUMS
    swing = dd["swing_ticks"]
    swing_steps = set(dd["swing_steps"])
    fill_cfg = d["drums"].get("fill", {})
    fill_every = fill_cfg.get("every_n_bars", 0)
    ev = []

    for b in range(n_bars):
        base = b * bar
        is_fill = fill_every and (b + 1) % fill_every == 0

        for hit in dd["hits"]:
            midi = note_map[hit["note"]]
            vel  = hit["velocity"]
            for step in hit["steps"]:
                push = swing if step in swing_steps else 0
                t = base + step * S + push
                # shaker: alternate velocity for odd steps
                v = vel if step % 2 == 0 else max(vel - 8, 20)
                note_on(ev, t, midi, S - 1, v, ch=9)

        if is_fill and fill_cfg:
            fill_midi = note_map[fill_cfg["note"]]
            for i, step in enumerate(fill_cfg["steps"]):
                v = fill_cfg["velocity_start"] + i * fill_cfg["velocity_ramp"]
                note_on(ev, base + step * S, fill_midi, S - 1, v, ch=9)
    return ev

if __name__ == "__main__":
    d = load("jazz_electronic")
    n = len(d["chords"])
    ch = d["channels"]
    pr = d["programs"]
    tracks = [
        build_track(keys_events(d), "Rhodes",     pr["keys"], ch["keys"], tempo_bpm=d["tempo"]),
        build_track(bass_events(d), "Synth Bass", pr["bass"], ch["bass"]),
        build_track(arp_events(d),  "Poly Arp",   pr["arp"],  ch["arp"]),
        build_track(drum_events(d), "Drums",      channel=ch["drums"]),
    ]
    write_midi(out_path("jazz_electronic.mid"), tracks)
    a = " ".join(c["name"] for c in d["chords"][:8])
    b = " ".join(c["name"] for c in d["chords"][8:])
    print(f"wrote jazz_electronic.mid — {n} bars of 4/4 at {d['tempo']} BPM (A/B form)")
    print(f"  A: {a}")
    print(f"  B: {b}")
    print("tracks: 1) Rhodes  2) Synth Bass  3) Poly Arp  4) Drums")

    if "--sheet" in sys.argv:
        from build_sheet import build_sheet
        build_sheet()
