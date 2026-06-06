"""Nocturne in E minor — "Lamplight". All musical content in data/nocturne.yaml."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.music import (load, note_to_midi, notes_to_midi, ql, note_on, cc,
                       build_track, write_midi, out_path)

TPB = 480
BAR = ql(1.5)    # 6/8 bar = 3 eighths = 1.5 quarter-lengths
EIGHTH = ql(0.5)

def _vel(d, bar_index):
    """Velocity for melody and LH by section (from dynamics table)."""
    dyn_map = {int(k): v for k, v in d["dynamics"].items()}
    label = "mp"
    for k in sorted(dyn_map):
        if bar_index >= k:
            label = dyn_map[k]
    return {"pp": 52, "p": 60, "mp": 78, "mf": 85, "f": 92}.get(label, 78)

def melody_track(d):
    melodies = {int(k): v for k, v in d["melodies"].items()}
    score = d["score"]
    ev = []
    t = 0
    last = len(score) - 1
    for i, (_, mel_ref) in enumerate(score):
        vel = _vel(d, i) + 4
        for entry in melodies[mel_ref]:
            pitch, dur_ql = entry
            dur = ql(dur_ql)
            m = note_to_midi(pitch)
            if m is not None:
                note_on(ev, t, m, dur, vel if i < last else 66)
            t += dur
    return build_track(ev, "Piano RH", program=0,
                       tempo_bpm=d["tempo"], time_sig=d["time_signature"])

def accomp_track(d):
    score = d["score"]
    voicings = d["voicings"]
    pattern = d["lh_arpeggio"]
    ev = []
    last = len(score) - 1
    for i, (chord_name, _) in enumerate(score):
        base = i * BAR
        v = voicings[chord_name]
        bass = note_to_midi(v["bass"])
        upper = notes_to_midi(v["upper"])
        arp = [bass] + upper
        lh_vel = _vel(d, i) - 26

        # sustain pedal: down at bar start, up just before the next bar
        cc(ev, base, 64, 127)
        cc(ev, base + BAR - 15, 64, 0)

        if i == last:
            # roll the final Picardy chord
            for j, m in enumerate(arp):
                note_on(ev, base + j * 30, m, BAR - j * 30, lh_vel + 4)
        else:
            for step, idx in enumerate(pattern):
                vel = lh_vel + (8 if idx == 0 else 0)
                note_on(ev, base + step * EIGHTH, arp[idx], EIGHTH, vel)
    return build_track(ev, "Piano LH")

def build_sheet(d, basename="nocturne"):
    from to_sheet import Sheet
    score = d["score"]
    voicings = d["voicings"]
    melodies = {int(k): v for k, v in d["melodies"].items()}
    pattern = d["lh_arpeggio"]
    dyn_map = {int(k): v for k, v in d["dynamics"].items()}
    last = len(score) - 1

    sh = Sheet(d["title"], subtitle=d.get("subtitle"),
               composer=d.get("composer"),
               time_signature=f"{d['time_signature'][0]}/{d['time_signature'][1]}",
               key_sig="e", tempo=("Andante espressivo", d["tempo"]))
    rh, lh = sh.part("treble"), sh.part("bass")

    for i, (chord_name, mel_ref) in enumerate(score):
        if i in dyn_map:
            rh.dyn(dyn_map[i])
        for entry in melodies[mel_ref]:
            pitch, dur_ql = entry
            m = note_to_midi(pitch)
            if m is None:
                rh.rest(dur_ql)
            else:
                rh.note(m, dur_ql, fermata=(i == last))

        v = voicings[chord_name]
        arp = [note_to_midi(v["bass"])] + notes_to_midi(v["upper"])
        if i == last:
            lh.chord(arp, 1.5, fermata=True)
        else:
            for idx in pattern:
                lh.note(arp[idx], 0.5)
    return sh.render(basename)

if __name__ == "__main__":
    d = load("nocturne")
    score = d["score"]
    write_midi(out_path("nocturne.mid"), [melody_track(d), accomp_track(d)])
    print(f"wrote nocturne.mid — {d['title']}, {len(score)} bars of 6/8 at {d['tempo']} BPM")
    print(f"  A:    {' '.join(c for c,_ in score[:8])}")
    print(f"  B:    {' '.join(c for c,_ in score[8:16])}")
    print(f"  A':   {' '.join(c for c,_ in score[16:24])}")
    print(f"  coda: {' '.join(c for c,_ in score[24:])}")
    print("tracks: 1) Piano RH  2) Piano LH — assign a single Grand Piano.")

    if "--sheet" in sys.argv:
        build_sheet(d)
        print("engraved output/nocturne.musicxml + output/nocturne.pdf")
